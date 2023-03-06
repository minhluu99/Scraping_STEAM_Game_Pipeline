import requests
import bs4
from bs4 import BeautifulSoup
import json
import pandas as pd
from argparse import Namespace

from datetime import datetime, timedelta
from textwrap import dedent
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.decorators import task
from airflow.utils.dates import days_ago

import sys
import pickle

max_recursion_depth = 10000
class recursion_depth:
    '''
    System just allow sys.getrecursionlimit() = 3000 by default.When Scraping from steam, 
    there is a huge size. This make pickle overload, even when transfer data from task to 
    next step in airflow.

    This Object helps to set recursion limit in several line, then it returns to default
    Manual: With recursion_depth(max_recursion_depth)
    '''
    def __init__(self, limit):
        self.limit = limit
        self.default_limit = sys.getrecursionlimit()
    def __enter__(self):
        sys.setrecursionlimit(self.limit)
    def __exit__(self, type, value, traceback):
        sys.setrecursionlimit(self.default_limit)


@task
def get_total_item(url):
    '''
    Get the number of games currently in steam. In this way we can calculate the number of pages
    '''
    data = requests.get(url).json()
    total_item = data['total_count']
    return total_item

@task
def get_data(url):
    '''
    Each page has information on 50 games. It is still html text and unprocessed,
    We will process to get the information of each game in the task below

    Returns list of html text for each game 
    '''
    data = requests.get(url).json()
    soup = BeautifulSoup(data['results_html'],'html.parser')
    games = soup.find_all('a')
    link = '/mnt/d/Github/Steam_ETL/src/intermediate_file.pickle'
    with recursion_depth(max_recursion_depth):
        with open(link,'wb') as f:
            pickle.dump(games,f)
    return link

@task
def parse(link):
    '''
    parse mean process html text to extract data for each game

    Returns the list of data of each game
    '''
    with recursion_depth(max_recursion_depth):
        with open(link,'rb') as f:
            games = pickle.load(f)
    list_games = []
    for game in games:
        idx = int(game.get('data-ds-appid'))
        name = game.find('span',{'class':'title'}).text
        platform = ', '.join(game.find('span',{'class':"platform_img"}).get('class')[1:])
        vr_supported = 'True' if game.find('span',{'class':"VR Supported"}) else False
        try: 
            release_date = game.find('div',{'class':"search_released"}).text
        except:
            release_date = None
        url = game.get('href').split('?snr=')[0]
        price = game.find('div',{'class':"search_price"}).text.strip().split('₫')[0]
        if price == 'Free to Play':
            price = '0'
        try:
            disprice = game.find('div',{'class':"search_price"}).text.strip().split('₫')[1]
        except:
            disprice = price
        review = game.find('span',{'class':"search_review_summary"}).get('data-tooltip-html')

        return_dict = {
            'id' : idx,
            'name' : name,
            'platform' : platform,
            'vr_supported': vr_supported,
            'release_date':release_date,
            'url':url,
            'price':price,
            'disprice':disprice,
            'review':review
        }    
        list_games.append(return_dict)

    return list_games

@task
def to_csv_file(game_list):
    '''
    Save to csv file by using pandas
    '''
    gamesdf = pd.DataFrame(game_list)
    gamesdf.to_csv('/mnt/d/Github/Steam_ETL/output_example/game_prices.csv',index=False)
    print('Saved to csv')



# defining DAG arguments
default_args = {
    'owner': 'minhluu99',
    'start_date': days_ago(0),
    # 'email': ['ramesh@somemail.com'],
    # 'email_on_failure': False,
    # 'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# define the DAG
with  DAG(
    'Steam_Dag_airflow',
    default_args=default_args,
    description='My first DAG',
    schedule_interval=timedelta(days=1),
) as dag:
    url = 'https://store.steampowered.com/search/results/?query&start=0&count=50&dynamic_data=&sort_by=_ASC&supportedlang=english&snr=1_7_7_230_7&infinite=1'
    # thís url is gotten by using searching in steam. But it's not just this easy
    # after using searching, you get "https://store.steampowered.com/search/?term="
    # Next, press F12 to open The Chrome Web Inspector and Debugger
    # Press Network, then in steam page, you slightly scroll down,
    # In Name block, it will appear the line have ?query...
    # click to that line then click Headers
    # the url is in Request URL

    link = get_data(url)
    game_list = parse( link)
    to_csv_file(game_list)