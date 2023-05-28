import asyncio
import logging
import warnings

from flask import Flask
from flask_mail import Mail, Message
from datetime import timedelta, datetime
import aiohttp
import pytz
import pymysql
import pandas as pd

from local_settings import *
from initialize_mysql import *


warnings.filterwarnings("ignore")

app = Flask(__name__)
app.config.from_object("local_settings")

email_service = Mail(app)


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


async def api_and_email_task(cityID, city_name, dateFact, tomorrow, delay_seconds, email_service, recipients):
    logging.info(f"starting async function `api_and_email_task` for {city_name}")
    logging.info(f"Entering timer of {delay_seconds} seconds")
    await asyncio.sleep(delay_seconds)
    logging.info(f"Exiting timer of {delay_seconds} seconds")
    
    async with aiohttp.ClientSession() as session:
        url = f"http://api.openweathermap.org/data/2.5/weather?id={cityID}&appid={OPENWEATHERMAP_AUTH['api_key']}"
        curr_r = await fetch(session, url)
        curr_obj = json.loads(curr_r)  # Parse the response as JSON

        today_weather = "-".join([curr_obj["weather"][0]["main"], curr_obj["weather"][0]["description"]])
        today_max_degrees_F = K_to_F(curr_obj["main"]["temp_max"])

        url = f"http://api.openweathermap.org/data/2.5/forecast?id={cityID}&appid={OPENWEATHERMAP_AUTH['api_key']}"
        forecast_r = await fetch(session, url)
        forecast_obj = json.loads(forecast_r)  # Parse the response as JSON

        tmrw_objs = [x for x in forecast_obj["list"] if x["dt_txt"][0:10] == tomorrow]
        tomorrow_max_degrees_F = K_to_F(max([tmrw_obj["main"]["temp_max"] for tmrw_obj in tmrw_objs]))

        query = "INSERT INTO klaviyo.tblFactCityWeather(city_id, dateFact, today_weather, today_max_degrees_F, tomorrow_max_degrees_F) VALUES (%s, %s, %s, %s, %s)"
        data = (cityID, dateFact, today_weather, today_max_degrees_F, tomorrow_max_degrees_F)
        run_query(mysql_conn, query, data)
        logging.info("updated klaviyo.tblactCityWeather")

        # Weather conditions and email subject/gifs
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

        messages = []
        for recipient in recipients:
            msg = Message(subject_value, recipients=[recipient], sender=app.config["MAIL_USERNAME"])
            msg.html = f"{city_name} - {today_max_degrees_F} degrees F - {today_weather} <br><br><img src='{gif_link}' width='640' height='480'>"
            messages.append(msg)

        with app.app_context():
            async with email_service.connect() as conn:
                conn.send(messages)

        logging.info(f"finished async function `api_and_email_task` for {city_name}")


async def main():
    tasks = []
    tz = pytz.timezone("US/Pacific")
    logging.Formatter.converter = lambda *args: datetime.now(tz).timetuple()

    logging.basicConfig(
        filename="/logs/api_and_async_email_20230527.log",
        format="%(asctime)s %(levelname)s: %(message)s",
        level=logging.INFO,
        datefmt=f"%Y-%m-%d %H:%M:%S ({tz})",
    )

    mysql_conn = getSQLConn(MYSQL_AUTH["host"], MYSQL_AUTH["user"], MYSQL_AUTH["password"])

    def run_query(mysql_conn, query, data=None):
        with mysql_conn.cursor() as cursor:
            if data:
                cursor.execute(query, data)
            else:
                cursor.execute(query)

    query = """DELETE from klaviyo.tblFactCityWeather where dateFact<date_sub(CURRENT_DATE, interval 60 day) or dateFact=CURRENT_DATE """
    run_query(mysql_conn, query)
    logging.info("finished purging weather data today and older than 60 days from klaviyo.tblFactCityWeather")

    query = """DELETE from klaviyo.tblDimEmailCity where sign_up_date<date_sub(CURRENT_DATE, interval 10 day) """
    run_query(mysql_conn, query)
    logging.info("finished purging data older than 10 days from klaviyo.tblDimEmailCity")

    tblDimEmailCity = pd.read_sql_query(
        """SELECT group_concat(convert(email,char)) AS email_set, city_id FROM klaviyo.tblDimEmailCity group by city_id""",
        con=mysql_conn,
    )

    dateFact = (datetime.now() + timedelta(1)).strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(2)).strftime("%Y-%m-%d")

    for row in tblDimEmailCity.itertuples(index=True, name="Pandas"):
        recipients = str(getattr(row, "email_set")).split(",")
        cityID = getattr(row, "city_id")
        city_name = city_dict[str(cityID)]
        delay_seconds = int(city_dict_nested[cityID]["u_offset_seconds"])
        logging.info(f"cityID={str(cityID)}, city_name={city_name}")

        task = asyncio.create_task(
            api_and_email_task(cityID, city_name, dateFact, tomorrow, delay_seconds, email_service, recipients)
        )
        tasks.append(task)

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
