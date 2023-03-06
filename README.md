# Scraping_STEAM_Game_Pipeline
This project is built for learning Apache_Airflow and Web_Scraper. This one scrap information of steam game.
I build this project on WSL stands for Windows Subsystem for Linux and visual studio code.

## Configuring environment
Step 1: Create python venv, ensure python version is 3.6,3.7 or 3.8. Because the requirement of Apache Airflow
<pre>python3.8 -m venv STEAM_linux</pre>

Step 2: Activate venv then install Apache Airflow
<pre>source STEAM_linux/bin/activate 
pip install 'apache-airflow==2.5.1' \
 --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.5.1/constraints-3.8.txt"
</pre>

Step 3: Set Airflow home is src dir in working path
<pre>echo "export AIRFLOW_HOME=\"$(pwd)/src\"" >> STEAM_Linux/bin/activate
source STEAM_linux/bin/activate
airflow db init</pre> 

Step 4: Replace the line declare dags_folder by following command
<pre>dags_folder = /mnt/d/Github/Steam_ETL/src/Pipeline</pre> 

Step 5: Create user for airflow then enter password you want to create, keep the line --role Admin
<pre>airflow users create \
          --username admin \
          --firstname FIRST_NAME \
          --lastname LAST_NAME \
          --role Admin \
          --email admin@example.org</pre>

Step 6: Use airflow scheduler to moniter DAGs and trigger tasks
<pre>airflow scheduler</pre>

Step 7: Open new terminal, then you can connect to airflow to see result
<pre>airflow webserver -p 8080</pre>