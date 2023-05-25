from flask import Flask
import asyncio
from local_settings import *
from initialize_mysql import *
from time import sleep
from flask_mail import Mail, Message
import pandas as pd
import logging
import requests
import time
import pytz
from datetime import timedelta, datetime
import gc
import pymysql
import warnings


warnings.filterwarnings("ignore")

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


async def api_and_email_task(
    cityID, city_name, dateFact, tomorrow, delay_seconds, recipients, app, email_service
):
    logging.info(f"starting async function `get_data_and_email_task` for {city_name}")
    # current weather api call
    r = requests.get(
        "http://api.openweathermap.org/data/2.5/weather?id=%s&appid=%s"
        % (cityID, OPENWEATHERMAP_AUTH["api_key"])
    )
    obj = r.json()
    today_weather = "-".join(
        [obj["weather"][0]["main"], obj["weather"][0]["description"]]
    )
    today_max_degrees_F = K_to_F(obj["main"]["temp_max"])
    time.sleep(0.5)  # reduce cadence of api calls
    # forecast weather api call
    r = requests.get(
        "http://api.openweathermap.org/data/2.5/forecast?id=%s&appid=%s"
        % (cityID, OPENWEATHERMAP_AUTH["api_key"])
    )
    obj = r.json()
    tmrw_objs = [x for x in obj["list"] if x["dt_txt"][0:10] == tomorrow]
    tomorrow_max_degrees_F = K_to_F(
        max([tmrw_obj["main"]["temp_max"] for tmrw_obj in tmrw_objs])
    )
    query = (
        "INSERT INTO klaviyo.tblFactCityWeather(city_id, dateFact, today_weather, today_max_degrees_F, \
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
    logging.info("updated klaviyo.tblactCityWeather")

    precipitation_words = ["mist", "rain", "sleet", "snow", "hail"]
    sunny_words = ["sunny", "clear"]
    if any(x in today_weather for x in sunny_words):
        logging.info("sunny")
        subject_value = "It's nice out! Enjoy a discount on us."
        gif_link = "https://media.giphy.com/media/nYiHd4Mh3w6fS/giphy.gif"
    elif today_F >= tomorrow_F + 5:
        logging.info("warm")
        subject_value = "It's nice out! Enjoy a discount on us."
        gif_link = "https://media.giphy.com/media/nYiHd4Mh3w6fS/giphy.gif"
    elif any(x in today_weather for x in precipitation_words):
        logging.info("precipitation")
        subject_value = "Not so nice out? That's okay, enjoy a discount on us."
        gif_link = "https://media.giphy.com/media/1hM7Uh46ixnsWRMA7w/giphy.gif"
    elif today_F + 5 <= tomorrow_F:
        logging.info("cold")
        subject_value = "Not so nice out? That's okay, enjoy a discount on us."
        gif_link = "https://media.giphy.com/media/26FLdaDQ5f72FPbEI/giphy.gif"
    else:
        logging.info("other")
        subject_value = "Enjoy a discount on us."
        gif_link = "https://media.giphy.com/media/3o6vXNLzXdW4sbFRGo/giphy.gif"
    with app.app_context():
        with email_service.connect() as conn:
            for recipient in recipients:
                msg = Message(
                    subject_value,
                    recipients=[recipient],
                    sender=app.config["MAIL_USERNAME"],
                )
                msg.html = """ %s - %s degrees F - %s <br><br><img src="%s" \
                width="640" height="480"> """ % (
                    city_name,
                    today_F,
                    today_weather,
                    gif_link,
                )
                try:
                    conn.send(msg)
                    logging.info(
                        f"""succeeded sending email to {recipient} with delay of {delay_seconds} seconds """
                    )
                except:
                    logging.error(
                        f"""failed to send email to {recipient} with delay of {delay_seconds} seconds """
                    )
    logging.info(f"finished async function `get_data_and_email_task` for {city_name}")


def timetz(*args):
    return datetime.now(tz).timetuple()


# log in PST
tz = pytz.timezone("US/Pacific")
logging.Formatter.converter = timetz

logging.basicConfig(
    filename="/logs/api_and_async_email_retry.log",
    format="%(asctime)s %(levelname)s: %(message)s",
    level=logging.INFO,
    datefmt=f"%Y-%m-%d %H:%M:%S ({tz})",
)


# connect to sql
def getSQLConn(host, user, password):
    return pymysql.connect(host=host, user=user, passwd=password, autocommit=True)


# convert Kelvin to Fahrenheit
def K_to_F(degrees_kelvin):
    return int((float(degrees_kelvin) * (9 / 5)) - 459.67)


mysql_conn = getSQLConn(MYSQL_AUTH["host"], MYSQL_AUTH["user"], MYSQL_AUTH["password"])


# run query
def runQuery(mysql_conn, query):
    with mysql_conn.cursor() as cursor:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            cursor.execute(query)


async def main():
    tasks = []
    # today's date
    dateFact = datetime.now().strftime("%Y-%m-%d")
    logging.info("dateFact=%s" % (dateFact))
    # tomorrow's date
    tomorrow = str((datetime.now() + timedelta(1)).strftime("%Y-%m-%d"))
    logging.info("tomorrow=%s" % (tomorrow))

    # truncate table tblFactCityWeather with current data and data older than 60 days
    query = """DELETE from klaviyo.tblFactCityWeather where dateFact<date_sub(CURRENT_DATE, interval 60 day) or dateFact=CURRENT_DATE """
    runQuery(mysql_conn, query)
    logging.info(
        "finished purging weather data older than 60 days from klaviyo.tblFactCityWeather"
    )
    # truncate table tblDimEmailCity with signup dates older than 10 days
    query = """DELETE from klaviyo.tblDimEmailCity where sign_up_date<date_sub(CURRENT_DATE, interval 10 day) """
    runQuery(mysql_conn, query)
    logging.info(
        "finished purging data older than 10 days from klaviyo.tblDimEmailCity"
    )
    # get only relevant city_id data from tblDimEmailCity
    tblDimEmailCity = pd.read_sql_query(
        """SELECT group_concat(convert(email,char)) AS email_set, city_id FROM klaviyo.tblDimEmailCity group by city_id""",
        con=mysql_conn,
    )
    # for future, loop through by delay_time, with no delay time first
    for row in tblDimEmailCity.itertuples(index=True, name="Pandas"):
        recipients = str(getattr(row, "email_set")).split(",")
        cityID = getattr(row, "city_id")
        city_name = city_dict[str(cityID)]
        logging.info(f"cityID={str(cityID)}, city_name={city_name}")

        task = asyncio.create_task(
            api_and_email_task(cityID, city_name, dateFact, tomorrow, 0, email_service, recipients, app)
        )
        tasks.append(task)

    await asyncio.gather(*tasks)


asyncio.run(main())
