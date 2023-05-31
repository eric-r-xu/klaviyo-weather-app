# libraries
import logging
import warnings
import json
from datetime import timedelta, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import requests
import pytz
import pymysql
import pandas as pd
import smtplib
from timezonefinder import TimezoneFinder
import time

# local libraries
from local_settings import *
from initialize_mysql import *

warnings.filterwarnings("ignore")

# run at 7:58 AM local time
LOCAL_TIME_HOUR = 7
LOCAL_TIME_MINUTE = 58


def run_query(mysql_conn, query, data=None):
    with mysql_conn.cursor() as cursor:
        if data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)


def fetch(url):
    response = requests.get(url)
    return response.text


def api_and_email_task(
    cityID, city_name, dateFact, tomorrow, recipients, local_tz, utc_offset_seconds
):
    logging.info(f"starting function `api_and_email_task` for {city_name}")

    local_time = datetime.now(local_tz)
    target_local_time = datetime(
        local_time.year,
        local_time.month,
        local_time.day,
        LOCAL_TIME_HOUR,
        LOCAL_TIME_MINUTE,
        0,
        tzinfo=local_tz,
    )


    # use tomorrow if today already passed
    if local_time > target_time:
        tomorrow = now + timedelta(days=1)
        local_time = datetime.tomorrow(local_tz)
        target_time = datetime(
            local_time.year,
            local_time.month,
            local_time.day,
            LOCAL_TIME_HOUR,
            LOCAL_TIME_MINUTE,
            0,
            tzinfo=local_tz,
        )

    # do not run until scheduled time
    while local_time < target_time:
        # heart every 2 minutes
        time.sleep(120)
        logging.info(f"current_time = {current_time} target_time = {target_time}")
        local_time = datetime.now(local_tz)

    url = f"http://api.openweathermap.org/data/2.5/weather?id={cityID}&appid={OPENWEATHERMAP_AUTH['api_key']}"
    curr_r = fetch(url)
    curr_obj = json.loads(curr_r)

    today_weather = "-".join(
        [curr_obj["weather"][0]["main"], curr_obj["weather"][0]["description"]]
    )
    today_max_degrees_F = int((float(curr_obj["main"]["temp_max"]) * (9 / 5)) - 459.67)

    url = f"http://api.openweathermap.org/data/2.5/forecast?id={cityID}&appid={OPENWEATHERMAP_AUTH['api_key']}"
    forecast_r = fetch(url)
    forecast_obj = json.loads(forecast_r)

    tmrw_objs = [x for x in forecast_obj["list"] if x["dt_txt"][0:10] == tomorrow]
    tomorrow_max_degrees_F = int(
        (float(max([tmrw_obj["main"]["temp_max"] for tmrw_obj in tmrw_objs])) * (9 / 5))
        - 459.67
    )

    query = "INSERT INTO klaviyo.tblFactCityWeather(city_id, dateFact, today_weather, today_max_degrees_F, tomorrow_max_degrees_F) VALUES (%s, %s, %s, %s, %s)"
    data = (
        cityID,
        dateFact,
        today_weather,
        today_max_degrees_F,
        tomorrow_max_degrees_F,
    )
    run_query(mysql_conn, query, data)
    logging.info("updated klaviyo.tblactCityWeather")

    precipitation_words = ["mist", "rain", "sleet", "snow", "hail"]
    sunny_words = ["sunny", "clear"]
    if any(x in today_weather for x in sunny_words):
        logging.info("sunny")
        subject_value = "It's nice out! Enjoy a discount on us."
        gif_link = "https://media.giphy.com/media/nYiHd4Mh3w6fS/giphy.gif"
    elif today_max_degrees_F >= tomorrow_max_degrees_F + 5:
        logging.info("warm")
        subject_value = "It's nice out! Enjoy a discount on us."
        gif_link = "https://media.giphy.com/media/nYiHd4Mh3w6fS/giphy.gif"
    elif any(x in today_weather for x in precipitation_words):
        logging.info("precipitation")
        subject_value = "Not so nice out? That's okay, enjoy a discount on us."
        gif_link = "https://media.giphy.com/media/1hM7Uh46ixnsWRMA7w/giphy.gif"
    elif today_max_degrees_F + 5 <= tomorrow_max_degrees_F:
        logging.info("cold")
        subject_value = "Not so nice out? That's okay, enjoy a discount on us."
        gif_link = "https://media.giphy.com/media/26FLdaDQ5f72FPbEI/giphy.gif"
    else:
        logging.info("other")
        subject_value = "Enjoy a discount on us."
        gif_link = "https://media.giphy.com/media/3o6vXNLzXdW4sbFRGo/giphy.gif"

    for recipient in recipients:
        message = MIMEMultipart()
        message["From"] = GMAIL_AUTH["mail_username"]
        message["To"] = recipient
        message["Subject"] = Header(subject_value, "utf-8")
        message.attach(
            MIMEText(
                f"{city_name} - {today_max_degrees_F} degrees F - {today_weather} <br><br><img src='{gif_link}' width='640' height='480'>",
                "html",
            )
        )

        with smtplib.SMTP(GMAIL_AUTH["mail_server"], 587) as server:
            server.starttls()
            server.login(GMAIL_AUTH["mail_username"], GMAIL_AUTH["mail_password"])
            server.send_message(message)
            logging.info(f"Sent email to {recipient}")

    logging.info(f"finished function `api_and_email_task` for {city_name}")


def main():
    tz = pytz.timezone("US/Pacific")
    logging.Formatter.converter = lambda *args: datetime.now(tz).timetuple()

    logging.basicConfig(
        filename="/logs/api_and_async_email_20230530.log",
        format="%(asctime)s %(levelname)s: %(message)s",
        level=logging.INFO,
        datefmt=f"%Y-%m-%d %H:%M:%S ({tz})",
    )

    logging.info(
        "------------------------------------------------------------------------"
    )
    logging.info(
        "------------------------------------------------------------------------"
    )

    dateFact = (datetime.now() + timedelta(1)).strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(2)).strftime("%Y-%m-%d")

    logging.info(f"dateFact = {dateFact}")
    logging.info(f"tomorrow = {tomorrow}")

    mysql_conn = getSQLConn(
        MYSQL_AUTH["host"], MYSQL_AUTH["user"], MYSQL_AUTH["password"]
    )

    query = f"""DELETE from klaviyo.tblFactCityWeather where dateFact<date_sub(CURRENT_DATE, interval 60 day) or dateFact=CURRENT_DATE or dateFact='{dateFact}' """
    run_query(mysql_conn, query)
    logging.info(
        "finished purging weather data today and older than 60 days from klaviyo.tblFactCityWeather"
    )

    query = """DELETE from klaviyo.tblDimEmailCity where sign_up_date<date_sub(CURRENT_DATE, interval 10 day) """
    run_query(mysql_conn, query)
    logging.info(
        "finished purging data older than 10 days from klaviyo.tblDimEmailCity"
    )

    tblDimEmailCity = pd.read_sql_query(
        """SELECT group_concat(convert(email,char)) AS email_set, city_id FROM klaviyo.tblDimEmailCity group by city_id""",
        con=mysql_conn,
    )

    tf = TimezoneFinder()
    _tz = []
    _utc_offset_seconds = []
    for row in tblDimEmailCity.itertuples(index=True, name="Pandas"):
        cityID = getattr(row, "city_id")
        city_name = city_dict[str(cityID)]
        lat = city_dict_nested[cityID]["lat"]
        lon = city_dict_nested[cityID]["lon"]
        try:
            _tz_value = tf.timezone_at(lng=lon, lat=lat)
            _tz_offset_seconds_value = int(
                ((tf.timezone(_tz_value)).localize(now)).utcoffset().total_seconds()
            )
        except Exception as e:
            logging.error(f"TimezoneFinder error for {lat} {lon} with {e}")
        _tz.append(_tz_value)
        _utc_offset_seconds.append(_tz_offset_seconds_value)

    tblDimEmailCity["tz"] = _tz
    tblDimEmailCity["utc_offset_seconds"] = _utc_offset_seconds
    tblDimEmailCity_sorted = tblDimEmailCity.sort_values("utc_offset_seconds")

    for row in tblDimEmailCity_sorted.itertuples(index=True, name="Pandas"):
        recipients = str(getattr(row, "email_set")).split(",")
        cityID = getattr(row, "city_id")
        local_tz = getattr(row, "tz")
        utc_offset_seconds = getattr(row, "utc_offset_seconds")
        city_name = city_dict[str(cityID)]
        logging.info(
            f"cityID={str(cityID)}, city_name={city_name}, local_tz={local_tz}, utc_offset_seconds={utc_offset_seconds}"
        )

        api_and_email_task(
            cityID,
            city_name,
            dateFact,
            tomorrow,
            recipients,
            local_tz,
            utc_offset_seconds,
        )

    


if __name__ == "__main__":
    main()
    logging.info("made it to the bitter end!")
    logging.info(
        "------------------------------------------------------------------------"
    )
    logging.info(
        "------------------------------------------------------------------------"
    )
