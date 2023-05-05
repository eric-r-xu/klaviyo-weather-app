import pymysql
import warnings
from local_settings import *

# connect to sql
def getSQLConn(host, user, password):
    return pymysql.connect(host=host, user=user, passwd=password, autocommit=True)


createSchema = "CREATE SCHEMA IF NOT EXISTS rain;"

createTblFactLatLongRain = """CREATE TABLE IF NOT EXISTS rain.TblFactLatLongRain  
( `timestampChecked` INT(11) NOT NULL,
 `localDateTimeChecked` VARCHAR(255) NOT NULL,
 `timestampUpdated` INT(11) NOT NULL,
 `localDateTimeUpdated` VARCHAR(255) NOT NULL,
`latitude` DECIMAL(5,4) NOT NULL DEFAULT '0.0000',
`longitude` DECIMAL(5,4) NOT NULL DEFAULT '0.0000',
`rain_mm_l90d` DECIMAL(5,1) NOT NULL DEFAULT '0.0',
`rain_mm_l60d` DECIMAL(5,1) NOT NULL DEFAULT '0.0',
`rain_mm_l30d` DECIMAL(5,1) NOT NULL DEFAULT '0.0',
`rain_mm_l7d` DECIMAL(5,1) NOT NULL DEFAULT '0.0',
`rain_mm_l3d` DECIMAL(5,1) NOT NULL DEFAULT '0.0',
`rain_mm_l1d` DECIMAL(5,1) NOT NULL DEFAULT '0.0',
`rain_mm_l3h` DECIMAL(5,1) NOT NULL DEFAULT '0.0',
`rain_mm_l1h` DECIMAL(5,1) NOT NULL DEFAULT '0.0',
PRIMARY KEY (`timestampChecked`,`timestampUpdated`,`latitude`,`longitude`),
KEY `idxLatitude` (`idxLatitude`),
KEY `idxLongitude` (`idxLongitude`)) 
ENGINE=InnoDB DEFAULT CHARSET=latin1;"""

mysql_conn = getSQLConn(MYSQL_AUTH["host"], MYSQL_AUTH["user"], MYSQL_AUTH["password"])

with mysql_conn.cursor() as cursor:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cursor.execute(createSchema)
        cursor.execute(createTblFactLatLongRain)
