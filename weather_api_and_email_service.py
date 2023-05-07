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
logging.basicConfig(
    filename="/logs/logfile.weather_api_and_email_service.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S %z",
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


# convert Kelvin to Fahrenheit
def K_to_F(degrees_kelvin):
    return int((float(degrees_kelvin) * (9 / 5)) - 459.67)


def weather_api_service(cityIDset, dateFact, tomorrow, mysql_conn, city_dict):
    # truncate table tblFactCityWeather with current data and data older than 10 days
    query = """DELETE from klaviyo.tblFactCityWeather where dateFact=CURRENT_DATE or dateFact<date_sub(CURRENT_DATE, interval 10 day) """
    runQuery(mysql_conn, query)
    for _i, cityID in enumerate(cityIDset):
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
        time.sleep(1.5)  # reduce cadence of api calls
        # forecast weather api call
        r = requests.get(
            "http://api.openweathermap.org/data/2.5/forecast?id=%s&appid=%s"
            % (cityID, OPENWEATHERMAP_AUTH["api_key"])
        )
        obj = r.json()
        # ony get objects for tmrw
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
    return logging.info("finished weather api service")


def weather_email_service(email_service, app, mysql_conn, city_dict):
    # truncate table tblDimEmailCity with subscriptions older than 10 days
    truncate_query = """DELETE from klaviyo.tblDimEmailCity where sign_up_date<date_sub(CURRENT_DATE, interval 10 day)  """
    runQuery(mysql_conn, truncate_query)

    # tblDimEmailCity --> pandas dataframe & constrain city ids to consider by data in tblDimEmailCity
    tblDimEmailCity = pd.read_sql_query(
        "SELECT email, city_id FROM klaviyo.tblDimEmailCity", con=mysql_conn
    )
    city_id_set = set(tblDimEmailCity["city_id"])

    city_id_string = str(city_id_set).replace("{", "").replace("}", "")

    # create tblFactCityWeather_dict for today's weather api data constrained to city_id_set
    tfcw_df = pd.read_sql_query(
        "SELECT city_id, today_weather, today_max_degrees_F, tomorrow_max_degrees_F \
		FROM klaviyo.tblFactCityWeather where dateFact=CURRENT_DATE and city_id in (%s)"
        % (city_id_string),
        con=mysql_conn,
    )
    tblFactCityWeather_dict = dict()
    zipped_array = zip(
        tfcw_df["city_id"],
        tfcw_df["today_weather"],
        tfcw_df["today_max_degrees_F"],
        tfcw_df["tomorrow_max_degrees_F"],
    )
    for city_id, today_weather, today_F, tomorrow_F in zipped_array:
        tblFactCityWeather_dict[city_id] = [
            str(today_weather).lower(),
            int(today_F),
            int(tomorrow_F),
        ]

    for city_id in city_id_set:
        gc.collect()
        # find set of recipients per city id
        _tblDimEmailCity = tblDimEmailCity[tblDimEmailCity["city_id"] == city_id]
        _tblDimEmailCity = _tblDimEmailCity.reset_index(drop=True)
        recipients = set(_tblDimEmailCity["email"])
        logging.info("recipients = %s" % recipients)
        today_weather = tblFactCityWeather_dict[city_id][0]
        today_F = tblFactCityWeather_dict[city_id][1]
        tomorrow_F = tblFactCityWeather_dict[city_id][2]

        # subject_value + gif_link logic
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
                        sender="eric.r.xu@gmail.com",
                    )
                    msg.html = """ %s - %s degrees F - %s <br><br><img src="%s" \
					width="640" height="480"> """ % (
                        city_dict[str(city_id)],
                        today_F,
                        today_weather,
                        gif_link,
                    )
                    try:
                        conn.send(msg)
                    except:
                        logging.error("failed to send to %s" % recipient)
    return logging.info("finished weather email service")


# today's date
dateFact = datetime.datetime.now().strftime("%Y-%m-%d")
# tomorrow's date
tomorrow = str((datetime.datetime.now() + datetime.timedelta(1)).strftime("%Y-%m-%d"))

# weather api service
weather_api_service(cityIDset, dateFact, tomorrow, mysql_conn, city_dict)

# weather email service
weather_email_service(email_service, app, mysql_conn, city_dict)
