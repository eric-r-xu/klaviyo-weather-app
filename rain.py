###### PACKAGES ######
import pandas as pd
import logging
import time
import dateutil.parser
import flask
import numpy as np
from functools import wraps
from flask import Flask, request, Response, render_template
import numpy as np
import math
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import initialize_mysql_rain
from flask_mysqldb import MySQL
from local_settings import *
##########################

# ensure info logs are printed
logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')

app = Flask(__name__)

limiter = Limiter(
  app,
  default_limits=["500 per day", "50 per hour"])

app.config['MYSQL_HOST'] = MYSQL_AUTH['host']
app.config['MYSQL_USER'] = MYSQL_AUTH['user']
app.config['MYSQL_PASSWORD'] = MYSQL_AUTH['password']
app.config['MYSQL_DB'] = 'rain'

mysql = MySQL(app)



# connect to sql
def getSQLConn(host, user, password):
    return pymysql.connect(host=host, user=user, passwd=password, autocommit=True)


def unixtime_to_pacific_datetime(unixtime_timestamp):
    # Create a timezone object for the Pacific timezone
    pacific_timezone = pytz.timezone("US/Pacific")
    # Convert the Unix timestamp to a datetime object in UTC timezone
    utc_datetime = datetime.datetime.utcfromtimestamp(unixtime_timestamp)

    # Convert the UTC datetime object to the Pacific timezone
    output = pacific_timezone.localize(utc_datetime).astimezone(pacific_timezone)
    return str(output)


mysql_conn = getSQLConn(MYSQL_AUTH["host"], MYSQL_AUTH["user"], MYSQL_AUTH["password"])

# run query
def runQuery(mysql_conn, query):
    with mysql_conn.cursor() as cursor:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cursor.execute(query)

            

@app.route('/rain')
def rain_html():
  try:
    query_result = runQuery(mysql_conn, "SELECT * FROM rain.TblFactLatLongRain")
  return str(query_result)


#--------- RUN WEB APP SERVER ------------#

# Start the app server on port 1080
app.debug = True
app.run(host='0.0.0.0', port=1080, threaded=True)
