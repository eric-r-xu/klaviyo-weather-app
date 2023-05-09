import pymysql
import warnings
from local_settings import *

# connect to sql
def getSQLConn(host, user, password):
	return pymysql.connect(host=host,\
		user=user,\
		passwd=password,
		autocommit=True)


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

mysql_conn = getSQLConn(MYSQL_AUTH['host'], MYSQL_AUTH['user'], MYSQL_AUTH['password'])

with mysql_conn.cursor() as cursor:
	with warnings.catch_warnings():
		warnings.simplefilter('ignore')
		cursor.execute(createSchema)
		cursor.execute(createTblDimEmailCity)
		cursor.execute(createTblFactCityWeather)
