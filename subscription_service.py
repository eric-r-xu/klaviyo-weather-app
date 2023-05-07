###### PACKAGES ######
import pandas as pd
import logging
import pytz
from pytz import timezone
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
import initialize_mysql
from flask_mysqldb import MySQL
from local_settings import *
from validate_email import validate_email
from validate_email.updater import update_builtin_blacklist

##########################


def timetz(*args):
    return datetime.now(tz).timetuple()


# logging datetime in PST
tz = timezone("US/Pacific")
logging.Formatter.converter = timetz

logging.basicConfig(
    filename="/logs/subscription_service.log",
    format="%(asctime)s %(levelname)s: %(message)s",
    level=logging.INFO,
    datefmt=f"%Y-%m-%d %H:%M:%S ({tz})",
)

app = Flask(__name__)

limiter = Limiter(app, default_limits=["200 per day", "50 per hour"])

app.config["MYSQL_HOST"] = MYSQL_AUTH["host"]
app.config["MYSQL_USER"] = MYSQL_AUTH["user"]
app.config["MYSQL_PASSWORD"] = MYSQL_AUTH["password"]
app.config["MYSQL_DB"] = "klaviyo"

mysql = MySQL(app)

# update email blacklist
update_builtin_blacklist(force=True, background=True)


@app.route("/klaviyo_weather_app")
def klaviyo_weather_app_html():
    return render_template("subscribe.html")


@app.route("/klaviyo_weather_app", methods=["POST"])
def klaviyo_weather_app_post():
    i_email = str(request.form["i_email"])
    is_valid = validate_email(
        email_address=i_email, check_format=True, check_blacklist=True
    )

    if is_valid == False:
        return str("Unable to validate email address: %s" % i_email)

    i_city = str(request.form["i_city"])
    if i_city not in valid_city_set:
        return "Please choose a valid city from the list of 100 most populous US cities"

    i_city_id, i_city_name = int(i_city.split(" : ")[1]), i_city.split(" : ")[0]
    cur = mysql.connection.cursor()
    try:
        logging.info(
            cur.execute(
                "INSERT INTO tblDimEmailCity(email, city_id) VALUES (%s, %s)",
                (i_email, i_city_id),
            )
        )
        mysql.connection.commit()
        cur.close()
    except Exception as error:
        error_message = str("Caught this error: " + repr(error))
        if error_message.count("Duplicate entry") > 0:
            return str(
                "Existing subscription found for %s and location %s" % (i_email, i_city)
            )
        else:
            return error_message
    return str(
        "SUCCESS! email: %s is now subscribed to weather powered emails for %s "
        % (i_email, i_city_name)
    )


# --------- RUN WEB APP SERVER ------------#

# Start the app server on port 1984
app.debug = True
app.run(host="0.0.0.0", port=1984, threaded=True)
