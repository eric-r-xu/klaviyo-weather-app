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

# local libraries
from local_settings import *
from initialize_mysql import *

warnings.filterwarnings("ignore")

MAX_CONCURRENCY = 3

def long_sleep_with_heartbeat(total_sleep_time, heartbeat_interval):
    intervals = total_sleep_time // heartbeat_interval
    for _ in range(intervals):
        time.sleep(heartbeat_interval)
        logging.info(f"Heartbeat")
    remaining_time = total_sleep_time % heartbeat_interval
    if remaining_time > 0:
        time.sleep(remaining_time)

def run_query(mysql_conn, query, data=None):
    with mysql_conn.cursor() as cursor:
        if data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)

def fetch(url):
    response = requests.get(url)
    return response.text

def api_and_email_task(sem, cityID, city_name, dateFact, tomorrow, delay_seconds, recipients):
    # Acquire the semaphore
    with sem:
        logging.info(f"starting function `api_and_email_task` for {city_name}")
        logging.info(f"Entering timer of {delay_seconds} seconds")
        long_sleep_with_heartbeat(delay_seconds, 60)
        logging.info(f"Exiting timer of {delay_seconds} seconds")

        session = requests.Session()

        url = f"http://api.openweathermap.org/data/2.5/weather?id={cityID}&appid={OPENWEATHERMAP_AUTH['api_key']}"
        curr_r = fetch(url)
        curr_obj = json.loads(curr_r)

        today_weather = "-".join([curr_obj["weather"][0]["main"], curr_obj["weather"][0]["description"]])
        today_max_degrees_F = int((float(curr_obj["main"]["temp_max"]) * (9 / 5)) - 459.67)

        url = f"http://api.openweathermap.org/data/2.5/forecast?id={cityID}&appid={OPENWEATHERMAP_AUTH['api_key']}"
        forecast_r = fetch(url)
        forecast_obj = json.loads(forecast_r)

        tmrw_objs = [x for x in forecast_obj["list"] if x["dt_txt"][0:10] == tomorrow]
        tomorrow_max_degrees_F = int(
            (float(max([tmrw_obj["main"]["temp_max"] for tmrw_obj in tmrw_objs])) * (9 / 5)) - 459.67
        )

        query = "INSERT INTO klaviyo.tblFactCityWeather(city_id, dateFact, today_weather, today_max_degrees_F, tomorrow_max_degrees_F) VALUES (%s, %s, %s, %s, %s)"
        data = (cityID, dateFact, today_weather, today_max_degrees_F, tomorrow_max_degrees_F)
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
            message["From"] = GMAIL_AUTH['mail_username']
            message["To"] = recipient
            message["Subject"] = Header(subject_value, 'utf-8')
            message.attach(MIMEText(f"{city_name} - {today_max_degrees_F} degrees F - {today_weather} <br><br><img src='{gif_link}' width='640' height='480'>", "html"))

            with smtplib.SMTP(GMAIL_AUTH['mail_server'], 587) as server:
                server.starttls()
                server.login(GMAIL_AUTH['mail_username'], GMAIL_AUTH['mail_password'])
                server.send_message(message)
                logging.info(f"Sent email to {recipient}")

        logging.info(f"finished function `api_and_email_task` for {city_name}")

def main():
    tasks = []
    tz = pytz.timezone("US/Pacific")
    logging.Formatter.converter = lambda *args: datetime.now(tz).timetuple()

    logging.basicConfig(
        filename="/logs/api_and_async_email_20230528.log",
        format="%(asctime)s %(levelname)s: %(message)s",
        level=logging.INFO,
        datefmt=f"%Y-%m-%d %H:%M:%S ({tz})",
    )

    dateFact = (datetime.now() + timedelta(1)).strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(2)).strftime("%Y-%m-%d")

    logging.info("------------------------------------------------------------------------")
    logging.info("------------------------------------------------------------------------")

    logging.info(f"dateFact = {dateFact}")
    logging.info(f"tomorrow = {tomorrow}")

    mysql_conn = getSQLConn(MYSQL_AUTH["host"], MYSQL_AUTH["user"], MYSQL_AUTH["password"])

    query = f"""DELETE from klaviyo.tblFactCityWeather where dateFact<date_sub(CURRENT_DATE, interval 60 day) or dateFact=CURRENT_DATE or dateFact='{dateFact}' """
    run_query(mysql_conn, query)
    logging.info("finished purging weather data today and older than 60 days from klaviyo.tblFactCityWeather")

    query = """DELETE from klaviyo.tblDimEmailCity where sign_up_date<date_sub(CURRENT_DATE, interval 10 day) """
    run_query(mysql_conn, query)
    logging.info("finished purging data older than 10 days from klaviyo.tblDimEmailCity")

    tblDimEmailCity = pd.read_sql_query(
        """SELECT group_concat(convert(email,char)) AS email_set, city_id FROM klaviyo.tblDimEmailCity group by city_id""",
        con=mysql_conn,
    )

    _delay_seconds = []
    for row in tblDimEmailCity.itertuples(index=True, name="Pandas"):
        cityID = getattr(row, "city_id")
        city_name = city_dict[str(cityID)]
        _delay_seconds.append(int(city_dict_nested[cityID]["u_offset_seconds"]))

    tblDimEmailCity['delay_seconds'] = _delay_seconds
    tblDimEmailCity_sorted = tblDimEmailCity.sort_values('delay_seconds')

    for row in tblDimEmailCity_sorted.itertuples(index=True, name="Pandas"):
        recipients = str(getattr(row, "email_set")).split(",")
        cityID = getattr(row, "city_id")
        city_name = city_dict[str(cityID)]
        delay_seconds = int(city_dict_nested[cityID]["u_offset_seconds"])
        logging.info(f"cityID={str(cityID)}, city_name={city_name}")

        api_and_email_task(sem, cityID, city_name, dateFact, tomorrow, delay_seconds, recipients)

    logging.info("------------------------------------------------------------------------")
    logging.info("------------------------------------------------------------------------")

if __name__ == "__main__":
    main()
