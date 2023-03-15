import requests
from bs4 import BeautifulSoup
import time
import os

from datetime import timedelta
from airflow import DAG
from airflow.providers.mysql.operators.mysql import MySqlOperator
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
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

# defining DAG arguments
default_args = {
    'owner': 'airflow',
    'start_date': days_ago(0),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# define the DAG
with  DAG(
    'Steam_Dag_airflow',
    default_args=default_args,
    schedule_interval=timedelta(weeks=1),
) as dag:
    
    # @task
    # def get_total_item(url):
    #     '''
    #     Get the number of games currently in steam. In this way we can calculate the number of pages
    #     '''
    #     data = requests.get(url).json()
    #     total_item = data['total_count']
    #     return total_item

    @task
    def get_data(url):
        '''
        Each page has information on 50 games. It is still html text and unprocessed,
        We will process to get the information of each game in the task below

        Returns list of html text for each game 
        '''
        print('Environ','-'*50)
        for i in os.environ:
            if 'SMTP' in i :
                print(i,': ',os.environ[i])

        data = requests.get(url).json()
        soup = BeautifulSoup(data['results_html'],'html.parser')
        games = soup.find_all('a')
        link = os.path.abspath('./Intermediate/Steam_Scraper.pickle')
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
            platform = ', '.join([i.get('class')[1] for i in game.find_all('span',{'class':"platform_img"})])

            release_date = game.find('div',{'class':"search_released"})
            if release_date is not None:
                release_date = release_date.text
                try:
                    release_date =  time.strptime(release_date.replace(',',''), "%d %b %Y")
                except:
                    release_date = time.strptime(release_date.replace(',',''), "%b %Y")
                release_date = time.strftime("%Y-%m-%d",release_date)

            url = game.get('href').split('?snr=')[0]
            price = game.find('div',{'class':"search_price"}).text.strip().split('₫')[0]
            if 'Free' in price:
                price = '0'
            price = price.replace('.','')
            
            try:
                disprice = game.find('div',{'class':"search_price"}).text.strip().split('₫')[1]
                if disprice == '':
                    disprice = price
                if 'Free' in disprice:
                    disprice = '0'
                disprice = disprice.replace('.','')
            except:
                disprice = price
            

            review = game.find('span',{'class':"search_review_summary"}).get('data-tooltip-html')

            return_dict = {
                'id' : idx,
                'name' : name,
                'platform' : platform,
                'release_date':release_date,
                'url':url,
                'price':price,
                'disprice':disprice,
                'review':review
            }    
            list_games.append(return_dict)
        return list_games
    
    
    @task.virtualenv(requirements=["pandas"], system_site_packages=False)
    def to_csv_file(list_games):
        '''
        Save to csv file by using pandas
        '''
        import pandas as pd
        import os
        gamesdf = pd.DataFrame(list_games)
        csv_file = os.path.abspath('./output_example/game_prices.csv')
        gamesdf.to_csv(csv_file,index=False)
        print('Saved to csv')

    @task
    def to_mysql_insert_file(list_games,database,table):
        with open(os.path.abspath('./Intermediate/SQLquery/Insert.sql'),'w') as f:
            f.write(f'Use {database};\n')

            columns_name = ', '.join(list_games[0].keys())
            f.write(f'Insert into {table} ({columns_name}) values\n')
            
            for i in range(len(list_games)):
                line = list(list_games[i].values())
                line = str(line).replace('[','(').replace(']',')')
                line = line.replace('\'\'','NULL')
                f.write(line)
                if i == len(list_games) - 1:
                    f.write('\n')
                else:
                    f.write(',\n')
            update_duplicate = ', '.join([f'{i}={i}'for i in list_games[0].keys()][1:])
            f.write(f"ON DUPLICATE KEY UPDATE {update_duplicate};")
        return

    # Mysql Task: Create Database, Table if not exists
    Create = MySqlOperator(
        task_id = 'create_db',
        mysql_conn_id="Minhluu_local",
        sql=open(os.path.abspath('./Intermediate/SQLquery/Create_Database_table.sql'),'r').read(),
        database='Airflowdb'
    )

    # Mysql Task: Insert into Database
    Insert = MySqlOperator(
        task_id = 'insert_db',
        mysql_conn_id="Minhluu_local",
        sql=open(os.path.abspath('./Intermediate/SQLquery/Insert.sql'),'r').read(),
        database='Airflowdb'
    )

    # send email:
    email = EmailOperator(
        task_id='send_email',
        to='LGMonline365@gmail.com',
        subject='SCRAPING_STEAM_GAME',
        html_content='<h1> Success! Here is 50 game in steam</h1>',
        files=[ os.path.abspath('./output_example/game_prices.csv')]
    )


    url = 'https://store.steampowered.com/search/results/?query&start=0&count=50&dynamic_data=&sort_by=_ASC&supportedlang=english&snr=1_7_7_230_7&infinite=1'
    # thís url is gotten by using searching in steam. But it's not just this easy
    # after using searching, you get "https://store.steampowered.com/search/?term="
    # Next, press F12 to open The Chrome Web Inspector and Debugger
    # Press Network, then in steam page, you slightly scroll down,
    # In Name block, it will appear the line have ?query...
    # click to that line then click Headers
    # the url is in Request URL

    link = get_data(url)
    game_list = parse(link)
    
    to_csv_file(game_list) >> email
    
    Create >> to_mysql_insert_file(game_list,'Airflowdb','Steam_games') >> Insert 


    
    