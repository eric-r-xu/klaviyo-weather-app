# [klaviyo-weather-app](https://www.klaviyo.com/weather-app)
## [Top 100 US Cities by Population from 2018 Estimate](https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population)
### web application deployment directions
#### Deployed Ubuntu 20.04 (LTS) x64 Digital Ocean droplet, git version 2.17.1, Python 3.6.9, & MySQL 5.7.41 
#### subscription app service hosted here: http://143.244.177.48:1984/klaviyo_weather_app
1. *ssh into your Ubuntu server*
2. *install MySQL (e.g. https://www.digitalocean.com/community/tutorials/how-to-install-mysql-on-ubuntu-20-04)*
3. > sudo apt-get update
4. > sudo apt-get upgrade
5. > sudo apt-get install git
6. > cd ~/
7. > git clone https://github.com/eric-r-xu/klaviyo-weather-app.git
8. *follow instructions in **local_settings_template.py** to set up api and mysql credentials and initialize city variables*
9. > sudo apt install -y python3-pip
10. > sudo apt-get install python3-setuptools
11. *install python3 virtual environment and packages using instructions below*
12. > cd klaviyo-weather-app;sudo apt-get install python3-venv
13. > sudo apt install build-essential libssl-dev libffi-dev python-dev-is-python3
14. > python3 -m venv env 
15. > source ./env/bin/activate
16. > python -m pip install --upgrade pip
17. > sudo apt-get install libsasl2-dev libsasl2-2 libsasl2-modules-gssapi-mit
18. > sudo apt-get install libmysqlclient-dev
19. > pip install -r ~/klaviyo-weather-app/py3requirements.txt
20. > python -m pip install git+https://gitea.ksol.io/karolyi/py3-validate-email@v1.0.9
21. *start the flask app subscription service send log messages to '/tmp/klaviyo-weather-app.subscription_service.log.$(date +\%Y\%m\%d)' using step 18*
22. > nohup python3 ~/klaviyo-weather-app/subscription_service.py > /tmp/klaviyo-weather-app.subscription_service.log.$(date +\%Y\%m\%d) &
23. *cron the daily weather api & email service and log messages to '/tmp/klaviyo-weather-app.weather_api_and_email_service.log.$(date +\%Y\%m\%d)' by adding step 20 into your crontab (e.g. `crontab -e`)*
24.  > ###### 0 9 * * * /home/$(whoami)/klaviyo-weather-app/env/bin/python3 /home/$(whoami)/klaviyo-weather-app/weather_api_and_email_service.py > /tmp/klaviyo-weather-app.weather_api_and_email_service.log.$(date +\%Y\%m\%d) 2>&1

-----------------------------------------------------------------------------------------------------------------------------

## Scalability 
##### What happens if your app launches and goes viral? What bottlenecks would there be and how can you optimize the system or break through them?

>Currently this web application is deployed using a shared CPU Ubuntu 18.04 LTS Digital Ocean droplet.  To control for high volume, the subscription page limits 50 requests per hour and 200 requests per day for each remote address.  If the app reaches resource limits due to to high traffic, optimizations include (but are not limited to):

>(a) upgrading the number of virtual CPUs (units of processing power) and RAM memory

>(c) switching from shared CPU to dedicated CPUs to minimize hyperthread data loss

>(c) hosting the web application on a WGSI server or a more production-ready Django web application framework to more efficiently handle concurrent requests/threads

>(d) separating the subscription app server from the weather api and the weather email servers

>(e) purging older subscriptions on a regular cadence to save on storage and compute (currently subscriptions older than 10 days are purged)

>(f) using a distributed relational database architecture like hive on a hadoop distributed file system to more gracefully handle larger amounts of data



## Security 
##### How does your app handle invalid or even malicious input from users?

>The subscription page checks for the validity of the email and limits the number of requests per remote address (50/hour and 200/day).  For edge cases not considered, please check the log file in /tmp/klaviyo-weather-app.subscription_service.log.$(date +\%Y\%m\%d)

## Re-Usability 
##### What components of your app would make sense to be their own modules or services so they can be re-used by other sections of code later?

>The weather powered email is comprised of 3 main components: 

>1st component: SUBSCRIPTION APPLICATION SERVICE -- renders the subscription form html, validates/limits requests, and maintains MySQL subscription table tblDimEmailCity

>2nd component: WEATHER API SERVICE -- calls weather api (https://www.weatherbit.io/api) and maintains MySQL table tblFactCityWeather

>3rd component: WEATHER EMAIL SERVICE -- purges old subscriptions in MySQL table tblDimEmailCity and sends weather powered emails based on MySQL tables tblDimEmailCity and tblFactCityWeather

>If the utilized Ubuntu 18.04 LTS server was upgraded to have >=4 gb RAM, a task scheduler service like airflow (https://airflow.apache.org/) could be useful to track and log the WEATHER API and WEATHER EMAIL services as their own operator tasks within a DAG.  The airflow webserver can then be started to log, track, and visualize task failures as well as task durations in an intuitive manner.  If more cpu/memory is needed to meet timing requirements, consider running airflow with a distributed architecture using Celery (see https://medium.com/@manuelmourato25/when-airflow-isnt-fast-enough-distributed-orchestration-of-multiple-small-workloads-with-celery-afb3daebe611).

## Re-Inventing the Wheel? 
##### We're big believers in not building what's already been built. Of course there are trade offs, so how did you decide whether to build functionality yourself or use existing solutions to make your job easier?

>I believe using mature open-source package solutions should be utilized as much as possible since it has the benefit of being thoroughly tested and furthers open-source package development.  However, building functionality yourself can be beneficial if:

>(a) more flexibility is needed than an open-source project currently allows 

>(b) you want to test and scale out your prototype manually before committing to any existing solutions that may be costly or overkill

>(c) time is critical & the language(s) and/or abstraction layer(s) are unfamiliar or complex

>The current weather app is built using Flask, a popular open-source microframework for creating flexible and lightweight web applications.  Instead of reinventing the wheel (or my own logic), I opted to use a popular python3 package for validating email addresses (https://pypi.org/project/py3-validate-email/) with added functionality such as domain validation and blacklist exclusion.


## Usability 
##### It's important that Klaviyo be easy to use — both for our users and the people they're emailing. How could your app be easier (or maybe more fun) to use?

>I believe the app could be easier & more intuitive to use by allowing users to specify what frequency and what local time they prefer to receive the weather powered email (currently, the emails are sent once daily starting at 9 am EDT).  Adding the functionality to subscribe more than one email at a time could also help with ease of use.


>I believe the weather powered email could be more fun/engaging to the subscribed users by displaying interesting factoids of weather data historically for each subscriber's city as well data on the other 99 US cities.  
