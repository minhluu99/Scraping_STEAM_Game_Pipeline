# for SMTP Host, we use gmail.
export AIRFLOW__SMTP__SMTP_HOST=smtp.gmail.com
export AIRFLOW__SMTP__SMTP_STARTTLS=TRUE
export AIRFLOW__SMTP__SMTP_SSL=False
export AIRFLOW__SMTP__SMTP_USER=your@email.com
# This is not the basic password, it is app api key. 
# then read The Gmail SMTP Server Method in https://www.gmass.co/blog/gmail-smtp/
export AIRFLOW__SMTP__SMTP_PASSWORD=your_api_key    #<generated-api-key>
export AIRFLOW__SMTP__SMTP_PORT=587
export AIRFLOW__SMTP__SMTP_MAIL_FROM=Airflow           #<your-from-email>