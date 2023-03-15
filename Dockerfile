FROM apache/airflow:2.5.2 
ADD requirements.txt . 
COPY dags/. dags/.
RUN pip install -r Requirements.txt