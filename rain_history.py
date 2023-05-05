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
last_30_days_mm, last_updated = 'n/a','n/a'

@app.route('/rain_history')
def rain_html():
  return render_template("rain.html", last_30_days_mm, last_updated)


#--------- RUN WEB APP SERVER ------------#

# Start the app server on port 1080
app.debug = True
app.run(host='0.0.0.0', port=1080, threaded=True)
