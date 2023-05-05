from flask import Flask
from flask_mail import Mail, Message
import pandas as pd
import logging
import requests
import time
from local_settings import *
import datetime
import gc
import pymysql
import warnings

app = Flask(__name__)
app.config.update(
    dict(
        DEBUG=True,
        MAIL_SERVER="smtp.gmail.com",
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USE_SSL=False,
        MAIL_USERNAME=GMAIL_AUTH["mail_username"],
        MAIL_PASSWORD=GMAIL_AUTH["mail_password"],
    )
)
email_service = Mail(app)

# ensure info logs are printed
logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(message)s",
    level=logging.INFO,
    datefmt="%m/%d/%Y %I:%M:%S %p",
)

# connect to sql
def getSQLConn(host, user, password):
    return pymysql.connect(host=host, user=user, passwd=password, autocommit=True)


mysql_conn = getSQLConn(MYSQL_AUTH["host"], MYSQL_AUTH["user"], MYSQL_AUTH["password"])

# run query
def runQuery(mysql_conn, query):
    with mysql_conn.cursor() as cursor:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cursor.execute(query)


def rain_api_service(mysql_conn):
    # truncate table tblFactCityWeather with current data and data older than 90 days
    query = """DELETE from rain.TblFactLatLongRain where localDateTimeUpdated<date_sub(CURRENT_DATE, interval 90 day) """
    runQuery(mysql_conn, query)
    # current Menlo Park weather api call
    lat, long = 39.21433, -122.0094
    r = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={long}&appid={OPENWEATHERMAP_AUTH["api_key"]}"
        % (lat, long, OPENWEATHERMAP_AUTH["api_key"])
    )
    obj = r.json()
    rain_mm_l1h = 0
    try:
      rain_mm_l1h = rainobj['rain']['1h']
    except: 
      pass
      
      
    '''
    `timestampChecked` INT(11) NOT NULL,
     `localDateTimeChecked` VARCHAR(255) NOT NULL,
     `timestampUpdated` INT(11) NOT NULL,
     `localDateTimeUpdated` VARCHAR(255) NOT NULL,
    `latitude` DECIMAL(5,4) NOT NULL DEFAULT '0.0000',
    `longitude` DECIMAL(5,4) NOT NULL DEFAULT '0.0000',
    `rain_mm_l90d` DECIMAL(5,1) NOT NULL DEFAULT '0.0',
    `rain_mm_l60d` DECIMAL(5,1) NOT NULL DEFAULT '0.0',
    `rain_mm_l30d` DECIMAL(5,1) NOT NULL DEFAULT '0.0',
    `rain_mm_l7d` DECIMAL(5,1) NOT NULL DEFAULT '0.0',
    `rain_mm_l3d` DECIMAL(5,1) NOT NULL DEFAULT '0.0',
    `rain_mm_l1d` DECIMAL(5,1) NOT NULL DEFAULT '0.0',
    `rain_mm_l3h` DECIMAL(5,1) NOT NULL DEFAULT '0.0',
    `rain_mm_l1h` DECIMAL(5,1) NOT NULL DEFAULT '0.0',
    '''
    query = (
        f"INSERT INTO rain.TblFactLatLongRain(city_id, dateFact, today_weather, today_max_degrees_F, \
tomorrow_max_degrees_F) VALUES (%i, '%s', '%s', %i, %i)"
        % (
            cityID,
            dateFact,
            today_weather,
            today_max_degrees_F,
            tomorrow_max_degrees_F,
        )
    )
        runQuery(mysql_conn, query)
        logging.info(
            "%s - %s - %s - %s - %s - %s"
            % (
                city_dict[str(cityID)],
                cityID,
                dateFact,
                today_weather,
                today_max_degrees_F,
                tomorrow_max_degrees_F,
            )
        )
        if _i % 20 == 5:
            gc.collect()
    return logging.info("finished calling weather api")


# weather api service
weather_api_service(mysql_conn)
