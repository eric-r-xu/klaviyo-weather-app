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
import pytz
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


def unixtime_to_pacific_datetime(unixtime_timestamp):
    # Create a timezone object for the Pacific timezone
    pacific_timezone = pytz.timezone("US/Pacific")
    # Convert the Unix timestamp to a datetime object in UTC timezone
    utc_datetime = datetime.datetime.utcfromtimestamp(unixtime_timestamp)

    # Convert the UTC datetime object to the Pacific timezone
    output = pacific_timezone.localize(utc_datetime).astimezone(pacific_timezone)
    return str(output)


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
        f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={long}&appid={OPENWEATHERMAP_AUTH["api_key"]}'
    )
    timestampChecked = int(time.time())

    api_result_obj = r.json()
    rain_mm_l1h, timestampUpdated = 0, api_result_obj["dt"]
    try:  # rain key will not be present if no rain
        rain_mm_l1h = api_result_obj["rain"]["1h"]
    except:
        pass

    query = (
        "INSERT INTO rain.TblFactLatLongRain(timestampChecked, localDateTimeChecked, timestampUpdated, localDateTimeUpdated, \
latitude, longitude, rain_mm_l1h) VALUES (%i, '%s', %i, '%s', %.4f, %.4f, %.1f)"
        % (
            timestampChecked,
            unixtime_to_pacific_datetime(timestampChecked),
            timestampUpdated,
            unixtime_to_pacific_datetime(timestampUpdated),
            lat,
            long,
            rain_mm_l1h,
        )
    )
    runQuery(mysql_conn, query)
    logging.info(
        "%s - %s - %s - %s - %s - %s - %s"
        % (
            timestampChecked,
            unixtime_to_pacific_datetime(timestampChecked),
            timestampUpdated,
            unixtime_to_pacific_datetime(timestampUpdated),
            lat,
            long,
            rain_mm_l1h,
        )
    )
    return logging.info("finished calling weather api and updating mysql")


# rain api service
rain_api_service(mysql_conn)
