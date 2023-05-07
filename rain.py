###### PACKAGES ######
import pandas as pd
import logging
import warnings
import pymysql
from pytz import timezone
import pytz
import time
import dateutil.parser
import flask
import datetime
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


def timetz(*args):
    return datetime.datetime.now(tz).timetuple()


# logging datetime in PST
tz = timezone("US/Pacific")
logging.Formatter.converter = timetz

logging.basicConfig(
    filename="/logs/rain.log",
    format="%(asctime)s %(levelname)s: %(message)s",
    level=logging.INFO,
    datefmt=f"%Y-%m-%d %H:%M:%S ({tz})",
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

@app.route("/rain")
def rain_home_html():
    return render_template("rain_update.html")


@app.route("/rain", methods=(["POST"]))
def rain_gen_html_table():
    df = pd.read_sql_query(
        """
        SELECT  
            "All" AS "Level",
            location_name AS "Location Name",
            convert_tz(FROM_UNIXTIME(dt),'UTC','US/Pacific') AS "Last Updated",
            convert_tz(FROM_UNIXTIME(requested_dt),'UTC','US/Pacific')) AS "Last Checked",
            rain_1h AS "1 hour rainfall in mm",
            rain_3h AS "3 hour rainfall in mm"
        FROM 
            rain.tblFactLatLon 
        ORDER BY 
            2 ASC, 
            3 DESC,
            4 DESC
        """,
        mysql_conn,
    )
    return render_template(
        "rain_all.html", tables=[df.to_html(classes="data")], titles=df.columns.values
    )


# --------- RUN WEB APP SERVER ------------#

# Start the app server on port 1080
app.debug = True
app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.run(host="0.0.0.0", port=1080, threaded=True)
