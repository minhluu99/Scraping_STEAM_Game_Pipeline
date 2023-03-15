# Scraping_STEAM_Game_Pipeline with Docker
This branch will confirguring with docker instead of wsl local

## Some detail had been confirguring
* The Dockerfile to install environment for image
* Create directory for saving result and intermediate files

![Connect_dir](output_example\Connect_dir.png)

* Add Mysql service to docker-compose.yaml and MySQL connection in airflow UI

![MySQL_service](output_example\MySQL_service.png)

* Add environment variables to allow sending email with SMTP

![SMTP_environment](output_example\SMTP_environment.png)

## Configuring Environment To Run

* Step 1: declare SMTP variables likes above

* Step 2: Run command
```console
docker compose up -d --build
```

* Step 3: Open UI Web App : http://localhost:8080/home

* Step 4: Create new account in mysql for airflow
```sql
CREATE DATABASE airflowdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'airflow' IDENTIFIED BY 'airflow';
GRANT ALL PRIVILEGES ON airflowdb.* TO 'airflow';
```

* Step 5: Create your new MySQL connection in airflow UI with mysql_conn_id = "Minhluu_local"
![](output_example\MySQL_connection.png)

It is all step to config

