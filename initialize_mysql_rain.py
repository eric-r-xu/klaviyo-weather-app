import pymysql
import warnings
from local_settings import *

# connect to sql
def getSQLConn(host, user, password):
    return pymysql.connect(host=host, user=user, passwd=password, autocommit=True)


createSchema = "CREATE SCHEMA IF NOT EXISTS rain;"

createTblFactLatLongRain = """CREATE TABLE IF NOT EXISTS rain.TblFactLatLongRain  
    (`timestampChecked` INT(11) NOT NULL,
    `localDateTimeChecked` VARCHAR(255) NOT NULL,
    `timestampUpdated` INT(11) NOT NULL,
    `localDateTimeUpdated` VARCHAR(255) NOT NULL,
    `latitude` DECIMAL(7,4) SIGNED NOT NULL DEFAULT '000.0000',
    `longitude` DECIMAL(7,4) SIGNED NOT NULL DEFAULT '000.0000',
    `rain_mm_l1h` DECIMAL(5,1) NOT NULL DEFAULT '0.0',
    PRIMARY KEY (`timestampChecked`,`timestampUpdated`,`latitude`,`longitude`)) 
    ENGINE=InnoDB DEFAULT CHARSET=latin1;"""

mysql_conn = getSQLConn(MYSQL_AUTH["host"], MYSQL_AUTH["user"], MYSQL_AUTH["password"])

with mysql_conn.cursor() as cursor:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cursor.execute(createSchema)
        cursor.execute(createTblFactLatLongRain)
