# libraries
import logging
import warnings
import json
from datetime import timedelta, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import requests
import asyncio
import gc
import pytz
import pymysql
import pandas as pd
import smtplib
import os
import psutil
from timezonefinder import TimezoneFinder
import time
import threading

# local libraries
from local_settings import *
from initialize_mysql import *

warnings.filterwarnings("ignore")

# run API and email at 8 AM local hour
LOCAL_TIME_HOUR = 8

# get process id for async garbage collection to prevent memory leaks
process = psutil.Process(os.getpid())


async def garbage_collection():
    while True:
        gc.collect()
        await asyncio.sleep(1800)  # Sleep for 1800 seconds, or 30 minutes


def run_garbage_collection():
    asyncio.run(garbage_collection())


def log_memory_usage():
    mem_info = process.memory_info()
    total_memory = psutil.virtual_memory().total
    memory_used_percentage = (mem_info.rss / total_memory) * 100
    # rss is the Resident Set Size and is used to show the portion of the process's memory held in RAM
    return logging.info(
        f"Memory used: {mem_info.rss}, Percentage of total memory: {round(memory_used_percentage,2)}%"
    )


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
    cityID, city_name, recipients, local_tz, utc_offset_seconds
):
    _local_tz = pytz.timezone(local_tz)
    local_time = datetime.now(_local_tz)
    local_tomorrow = str(local_time + timedelta(days=1)).strftime("%Y-%m-%d")
    local_dateFact = str(local_time.strftime("%Y-%m-%d"))
    local_hour = local_time.hour + 1
    local_dateFact_hour = local_dateFact + ' ' + str(local_hour)
    
    logging.info(f"starting function `api_and_email_task` for {city_name} with local date hour {local_dateFact_hour} and local tomorrow {local_tomorrow}")
    logging.info(f"{city_name} has local time = {str(local_time)}")
    
    # script runs hourly, so skipping cities not within hour
    if local_hour != LOCAL_TIME_HOUR
        return logging.info(
            f"skipping function `api_and_email_task` for {city_name} since local hour local_hour = {local_hour} is not LOCAL_TIME_HOUR = {LOCAL_TIME_HOUR}"
        )

    # call current weather api for city
    url = f"http://api.openweathermap.org/data/2.5/weather?id={cityID}&appid={OPENWEATHERMAP_AUTH['api_key']}"
    curr_r = fetch(url)
    curr_obj = json.loads(curr_r)

    today_weather = "-".join(
        [curr_obj["weather"][0]["main"], curr_obj["weather"][0]["description"]]
    )
    today_max_degrees_F = int((float(curr_obj["main"]["temp_max"]) * (9 / 5)) - 459.67)
    logging.info(
        f"{city_name}: today_weather = {today_weather}; {city_name} today_max_degrees_F = {today_max_degrees_F}"
    )

    # call forecast weather api for city
    url = f"http://api.openweathermap.org/data/2.5/forecast?id={cityID}&appid={OPENWEATHERMAP_AUTH['api_key']}"
    forecast_r = fetch(url)
    forecast_obj = json.loads(forecast_r)

    tmrw_objs = [x for x in forecast_obj["list"] if x["dt_txt"][0:10] == local_tomorrow]
    tomorrow_max_degrees_F = int(
        (float(max([tmrw_obj["main"]["temp_max"] for tmrw_obj in tmrw_objs])) * (9 / 5))
        - 459.67
    )
    logging.info(f"{city_name}: tomorrow_max_degrees_F = {tomorrow_max_degrees_F}")
    
    query = f"DELETE from klaviyo.tblFactCityWeather where dateFact='{local_dateFact}' and city_id={cityID} "
    run_query(mysql_conn, query)
    logging.info(
        f"successfully finished DELETE from klaviyo.tblFactCityWeather where dateFact='{local_dateFact}' and city_id={cityID} "
    )

    query = "INSERT INTO klaviyo.tblFactCityWeather(city_id, dateFact, today_weather, today_max_degrees_F, tomorrow_max_degrees_F) VALUES (%s, %s, %s, %s, %s)"
    data = (
        cityID,
        local_dateFact,
        today_weather,
        today_max_degrees_F,
        tomorrow_max_degrees_F,
    )
    run_query(mysql_conn, query, data)
    logging.info(f"successfully finished INSERT INTO klaviyo.tblFactCityWeather({str(cityID)}, {str(local_dateFact)}, {str(today_weather)}, {str(today_max_degrees_F)}, {str(tomorrow_max_degrees_F)})")

    precipitation_words = ["mist", "rain", "sleet", "snow", "hail"]
    sunny_words = ["sunny", "clear"]
    if any(x in today_weather for x in sunny_words):
        logging.info("sunny")
        subject_value = f"WEATHER APP: It's nice out in {city_name}!"
        gif_link = "https://media.giphy.com/media/nYiHd4Mh3w6fS/giphy.gif"
    elif today_max_degrees_F >= tomorrow_max_degrees_F + 5:
        logging.info("warm")
        subject_value = f"WEATHER APP: It's nice out in {city_name}!"
        gif_link = "https://media.giphy.com/media/nYiHd4Mh3w6fS/giphy.gif"
    elif any(x in today_weather for x in precipitation_words):
        logging.info("precipitation")
        subject_value = f"WEATHER APP: Not so nice out in {city_name}? That's okay."
        gif_link = "https://media.giphy.com/media/1hM7Uh46ixnsWRMA7w/giphy.gif"
    elif today_max_degrees_F + 5 <= tomorrow_max_degrees_F:
        logging.info("cold")
        subject_value = f"WEATHER APP: Not so nice out in {city_name}? That's okay."
        gif_link = "https://media.giphy.com/media/26FLdaDQ5f72FPbEI/giphy.gif"
    else:
        logging.info("other")
        subject_value = f"WEATHER APP: {city_name}"
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

        query = f"DELETE from klaviyo.tblDimEmailCity where sign_up_date<date_sub('{local_dateFact}', interval 10 day) and city_id={cityID} "
        run_query(mysql_conn, query)
        logging.info(
            f"finished {query}"
        )
    return logging.info(f"finished function `api_and_email_task` for {city_name}")


def main():
    # logging is in US pacific time
    tz = pytz.timezone("US/Pacific")
    logging.Formatter.converter = lambda *args: datetime.now(tz).timetuple()
    dateFact = str((datetime.now(tz)).strftime("%Y-%m-%d"))
    run_date_hour = dateFact + ' ' + str((datetime.now(tz)).strftime("%Y-%m-%d").hour + 1)
    
    logging.basicConfig(
        filename="/logs/api_and_email_service_hourly.log",
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
    
    logging.info(f"starting api_and_email_service_hourly.py for {run_date_hour}")

    mysql_conn = getSQLConn(
        MYSQL_AUTH["host"], MYSQL_AUTH["user"], MYSQL_AUTH["password"]
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
            if _tz_value is None:
                logging.error(f"No timezone found for {lat} {lon}")
                continue
            _tz.append(_tz_value)
            logging.info(f"found {_tz_value} as timezone for {lat} {lon}")
            try:
                # Get the current UTC time
                _now_utc = datetime.now(pytz.UTC)
                now_utc = _now_utc.replace(tzinfo=None)

                # Create the timezone
                _timezone = pytz.timezone(_tz_value)

                # Localize the time
                _localized_time = _timezone.localize(now_utc)

                # Get the UTC offset in seconds
                _utc_offset_seconds_value = _localized_time.utcoffset().total_seconds()
                _utc_offset_seconds.append(_utc_offset_seconds_value)
            except pytz.UnknownTimeZoneError:
                logging.error(f"Unknown timezone {_tz_value} for {lat} {lon}")
            except Exception as e:
                logging.error(
                    f"utc offset seconds calculation error for {lat} {lon} at timezone {_tz_value}. Error: {str(e)}"
                )
        except Exception as e:
            logging.error(f"TimezoneFinder error for {lat} {lon}. Error: {str(e)}")

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
            recipients,
            local_tz,
            utc_offset_seconds,
        )
    logging.info(f"finished api_and_email_service_hourly.py for {run_date_hour}")
    logging.info(
        "------------------------------------------------------------------------"
    )
    logging.info(
        "------------------------------------------------------------------------"
    )


# Run main() in the main thread
main()

# Run garbage_collection() in a different thread
gc_thread = threading.Thread(target=run_garbage_collection)
gc_thread.start()