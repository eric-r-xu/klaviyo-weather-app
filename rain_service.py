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
import initialize_mysql_rain
from initialize_mysql_rain import location_names

##########################


def timetz(*args):
    return datetime.datetime.now(tz).timetuple()


# logging datetime in PST
tz = timezone("US/Pacific")
logging.Formatter.converter = timetz

logging.basicConfig(
    filename="/logs/rain_service.log",
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
    return render_template("rain_service.html", location_names=location_names)


@app.route("/rain", methods=(["POST"]))
def rain_gen_html_table():
    i_location_name = str(request.form["i_location_name"])
    df = pd.read_sql_query(
        f"""
        SELECT  
            location_name AS "Location Name",
            CONVERT_TZ(FROM_UNIXTIME(dt),'UTC','US/Pacific') AS "Last Updated Time (PST)",
            MAX(CONVERT_TZ(FROM_UNIXTIME(requested_dt),'UTC','US/Pacific')) AS "Last Checked Time (PST)",
            MAX(rain_1h) AS "mm Rain Last Hour",
            MAX(rain_3h) AS "mm Rain Last 3 Hours"
        FROM 
            rain.tblFactLatLon 
        WHERE 
            location_name = "{i_location_name}" 
        GROUP BY 
            1, 2
        ORDER BY 
            2 DESC
        """,
        mysql_conn,
    )
    return render_template(
        "rain_service_result.html", tables=[df.to_html(classes="data")], titles=df.columns.values
    )


# --------- RUN WEB APP SERVER ------------#

# Start the app server on port 1080
app.debug = True
app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.run(host="0.0.0.0", port=1080, threaded=False, processes=3)
