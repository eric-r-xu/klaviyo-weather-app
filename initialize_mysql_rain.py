import pymysql
import warnings
import pandas as pd
import datetime
import pytz
from local_settings import *

# connect to sql
def getSQLConn(host, user, password):
    return pymysql.connect(host=host, user=user, passwd=password, autocommit=True)


createSchema = "CREATE SCHEMA IF NOT EXISTS rain;"

createTblFactLatLon = """CREATE TABLE IF NOT EXISTS rain.tblFactLatLon
    (`dt` INT(11) NOT NULL COMMENT 'unixtimestamp of last api data update',
    `updated_pacific_time` VARCHAR(255) NOT NULL COMMENT 'Pacific timezone datetime of last api data update',
    `requested_pacific_time` VARCHAR(255) COMMENT 'Pacific timezone datetime of last api data request',
    `location_name` VARCHAR(255) NOT NULL COMMENT 'label given for latitude longitude coordinate (e.g. bedwell bayfront park)',
    `lat` DECIMAL(7,3) SIGNED NOT NULL COMMENT 'latitude coordinate',
    `lon` DECIMAL(7,3) SIGNED NOT NULL COMMENT 'longitude coordinate',
    `rain_1h` DECIMAL(5,1) NOT NULL COMMENT 'mm rainfall in last hour',
    `rain_3h` DECIMAL(5,1) NOT NULL COMMENT 'mm rainfall in last 3 hours', 
    PRIMARY KEY (`dt`,`lat`,`lon`)) 
    ENGINE=InnoDB DEFAULT CHARSET=latin1;"""

mysql_conn = getSQLConn(MYSQL_AUTH["host"], MYSQL_AUTH["user"], MYSQL_AUTH["password"])

with mysql_conn.cursor() as cursor:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cursor.execute(createSchema)
        cursor.execute(createTblFactLatLon)


def unixtime_to_pacific_datetime(unixtime_timestamp):
    # Create a timezone object for the Pacific timezone
    pacific_timezone = pytz.timezone("US/Pacific")
    # Convert the Unix timestamp to a datetime object in UTC timezone
    utc_datetime = datetime.datetime.utcfromtimestamp(unixtime_timestamp)

    # Convert the UTC datetime object to the Pacific timezone
    output = pacific_timezone.localize(utc_datetime).astimezone(pacific_timezone)
    return str(output)


df = pd.read_csv("initial_data.csv").fillna(0)
requested_pacific_time = "2023-05-06"
for index, row in df.iterrows():
    query = (
        "INSERT INTO rain.tblFactLatLon(dt, updated_pacific_time, requested_pacific_time, location_name, lat, lon, rain_1h, rain_3h) VALUES (%i, '%s', '%s', '%s', %.3f, %.3f, %.1f, %.1f)"
        % (
            row["dt"],
            unixtime_to_pacific_datetime(int(row["dt"])),
            requested_pacific_time,
            row["location_name"],
            row["lat"],
            row["lon"],
            row["rain_1h"],
            row["rain_3h"],
        )
    )
    logging.info("query=%s" % (query))
    runQuery(mysql_conn, query)
    logging.info(
        "%s - %s - %s - %s - %s - %s - %s - %s"
        % (
            row["dt"],
            unixtime_to_pacific_datetime(int(row["dt"])),
            requested_pacific_time,
            row["location_name"],
            row["lat"],
            row["lon"],
            row["rain_1h"],
            row["rain_3h"],
        )
    )
logging.info("finished preload")
