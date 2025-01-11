import pymysql
import pandas as pd
import warnings
from local_settings import *


# connect to sql
def getSQLConn(host, user, password):
    return pymysql.connect(host=host, user=user, passwd=password, autocommit=True)


createSchema = "CREATE SCHEMA IF NOT EXISTS klaviyo;"

createTblDimEmailCity = """CREATE TABLE IF NOT EXISTS klaviyo.tblDimEmailCity 
( `email` VARCHAR(255) NOT NULL DEFAULT '0' COMMENT 'subscription email',
`city_id` INT(10) unsigned NOT NULL DEFAULT '0' COMMENT 'city id from api.openweathermap.org',
`sign_up_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'signup UTC datetime',
PRIMARY KEY (`email`, `city_id`),
KEY `idxEmail` (`email`),
KEY `idxCityID` (`city_id`)) 
ENGINE=InnoDB DEFAULT CHARSET=latin1;"""

createTblFactCityWeather = """CREATE TABLE IF NOT EXISTS klaviyo.tblFactCityWeather  
( `city_id` INT(10) NOT NULL DEFAULT '0',
`dateFact` date NOT NULL,
`today_weather` VARCHAR(255) NOT NULL DEFAULT '0',
`today_max_degrees_F` int(10) NOT NULL DEFAULT '0',
`tomorrow_max_degrees_F` int(10) NOT NULL DEFAULT '0',
PRIMARY KEY (`city_id`,`dateFact`),
KEY `idxDateFact` (`dateFact`),
KEY `idxCityID` (`city_id`)) 
ENGINE=InnoDB DEFAULT CHARSET=latin1;"""

mysql_conn = getSQLConn(MYSQL_AUTH["host"], MYSQL_AUTH["user"], MYSQL_AUTH["password"])

with mysql_conn.cursor() as cursor:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cursor.execute(createSchema)
        cursor.execute(createTblDimEmailCity)
        cursor.execute(createTblFactCityWeather)


dtype_options = {
    "id": int,
    "name": str,
    "state": str,
    "country": str,
    "lat": float,
    "lon": float,
    "u_offset_seconds": float,
}

# Import the CSV file with specified data types
df = pd.read_csv("/root/klaviyo-weather-app/city_dict.tsv", sep="\t", dtype=dtype_options)

df = df.fillna("")


city_dict = {
    str(_id): "".join([str(_name), " ", str(_state), "; ", str(_country)])
    for _id, _name, _state, _country in zip(
        df["id"], df["name"], df["state"], df["country"]
    )
}

city_dict_nested = df.set_index("id").T.to_dict()

cityIDset = {int(x) for x in city_dict.keys()}
cityNameSet = {str(x) for x in city_dict.values()}
city_name_to_id = {v: k for k, v in city_dict.items()}
