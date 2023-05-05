###### PACKAGES ######
import pandas as pd
import logging
import warnings
import pymysql
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
logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(message)s",
    level=logging.INFO,
    datefmt="%m/%d/%Y %I:%M:%S %p",
)

app = Flask(__name__)

limiter = Limiter(app, default_limits=["500 per day", "50 per hour"])

app.config["MYSQL_HOST"] = MYSQL_AUTH["host"]
app.config["MYSQL_USER"] = MYSQL_AUTH["user"]
app.config["MYSQL_PASSWORD"] = MYSQL_AUTH["password"]
app.config["MYSQL_DB"] = "rain"

mysql = MySQL(app)

# connect to sql
def getSQLConn(host, user, password):
    return pymysql.connect(host=host, user=user, passwd=password, autocommit=True)


# run query
def runQuery(mysql_conn, query):
    with mysql_conn.cursor() as cursor:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cursor.execute(query)


mysql_conn = getSQLConn(MYSQL_AUTH["host"], MYSQL_AUTH["user"], MYSQL_AUTH["password"])


@app.route("/", methods=("POST", "GET"))
def html_table():
    df = pd.read_sql_query(
        """
        SELECT  
            convert_tz(FROM_UNIXTIME(timestampUpdated),'UTC','US/Pacific') AS "Last Updated",
            convert_tz(FROM_UNIXTIME(timestampChecked),'UTC','US/Pacific') AS "Last Checked",
            rain_mm_l1h AS "Hourly Rainfall in mm"
        FROM 
            rain.TblFactLatLongRain 
        ORDER BY 
            1 DESC, 
            2 DESC
        """,
        mysql_conn,
    )
    return render_template(
        "rain.html", tables=[df.to_html(classes="data")], titles=df.columns.values
    )


# --------- RUN WEB APP SERVER ------------#

# Start the app server on port 1080
app.debug = True
app.run(host="0.0.0.0", port=1080, threaded=True)
