import pymysql
import warnings
from local_settings import *

# connect to sql
def getSQLConn(host, user, password):
    return pymysql.connect(host=host, user=user, passwd=password, autocommit=True)


createSchema = "CREATE SCHEMA IF NOT EXISTS rain;"

createTblFactLatLon = """CREATE TABLE IF NOT EXISTS rain.tblFactLatLon
    (`dt` INT(11) NOT NULL COMMENT 'unixtimestamp of last api data update',
    `updated_pacific_time` VARCHAR(255) NOT NULL COMMENT 'Pacific timezone datetime of last api data update',
    `requested_pacific_time` VARCHAR(255) NOT NULL COMMENT 'Pacific timezone datetime of last api data request',
    `location_name` VARCHAR(255) NOT NULL COMMENT 'label given for latitude longitude coordinate (e.g. bedwell bayfront park)',
    `lat` DECIMAL(7,3) SIGNED NOT NULL COMMENT 'latitude coordinate',
    `lon` DECIMAL(7,3) SIGNED NOT NULL COMMENT 'longitude coordinate',
    `rain_1h` DECIMAL(5,1) NOT NULL COMMENT 'mm rainfall in last hour',
    `rain_3h` DECIMAL(5,1) NOT NULL COMMENT 'mm rainfall in last 3 hours', 
    PRIMARY KEY (`timestampChecked`,`timestampUpdated`,`latitude`,`longitude`)) 
    ENGINE=InnoDB DEFAULT CHARSET=latin1;"""

mysql_conn = getSQLConn(MYSQL_AUTH["host"], MYSQL_AUTH["user"], MYSQL_AUTH["password"])

with mysql_conn.cursor() as cursor:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cursor.execute(createSchema)
        cursor.execute(createTblFactLatLon)
