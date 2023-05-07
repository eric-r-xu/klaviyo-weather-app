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
import initialize_mysql_rain

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


def timetz(*args):
    return datetime.datetime.now(tz).timetuple()


# logging datetime in PST
tz = timezone("US/Pacific")
logging.Formatter.converter = timetz

logging.basicConfig(
    filename="/logs/rain_api.log",
    format="%(asctime)s %(levelname)s: %(message)s",
    level=logging.INFO,
    datefmt=f"%Y-%m-%d %H:%M:%S ({tz})",
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

lat_lon_dict = {
    "Bedwell Bayfront Park": {"lat": 37.493, "lon": -122.173},
    "Urbana, Illinois": {"lat": 40.113, "lon": -88.211},
}


# run query
def runQuery(mysql_conn, query):
    with mysql_conn.cursor() as cursor:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cursor.execute(query)


def rain_api_service(mysql_conn, lat_lon_dict):
    runQuery(mysql_conn, query)
    api_key = OPENWEATHERMAP_AUTH["api_key"]
    for place_name in [each for each in lat_lon_dict.keys()]:
        logging.info(f"starting api call for {place_name}")
        lat, lon, api_key = (
            lat_lon_dict[place_name]["lat"],
            lat_lon_dict[place_name]["lon"],
        )
        api_link = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={long}&appid={api_key}"
        r = requests.get(api_link)
        logging.info("query=%s" % (query))
        timestampChecked = int(time.time())
        api_result_obj = r.json()
        rain_1h, rain_3h, timestampUpdated = 0, 0, api_result_obj["dt"]
        try:
            rain_1h = api_result_obj["rain"]["1h"]
        except:
            pass
        try:
            rain_3h = api_result_obj["rain"]["3h"]
        except:
            pass

        query = (
            "INSERT INTO rain.TblFactLatLongRain(timestampChecked, localDateTimeChecked, timestampUpdated, localDateTimeUpdated, latitude, longitude, rain_mm_l1h) VALUES (%i, '%s', %i, '%s', %.4f, %.4f, %.1f)"
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
        logging.info("query=%s" % (query))
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
