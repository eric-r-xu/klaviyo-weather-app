# [klaviyo-weather-app](https://www.klaviyo.com/weather-app)
## [Top 100 US Cities by Population from 2018 Estimate](https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population)
### web application deployment directions
#### Deployed using a shared CPU Ubuntu 18.04 LTS Digital Ocean droplet, git version 2.17.1, Python 3.6.8, & MySQL 5.7.27 and subscription app service hosted here: http://104.236.40.7:1984/klaviyo_weather_app
1. *ssh into your Ubuntu 18.04 LTS server*
2. *install MySQL (e.g. https://www.digitalocean.com/community/tutorials/how-to-install-mysql-on-ubuntu-18-04)*
3. > sudo apt-get update
4. > sudo apt-get upgrade
5. > sudo apt-get install git
6. > cd ~/
7. > git clone https://github.com/eric-xu-ownerIQ/klaviyo-weather-app.git
8. *follow instructions in **local_settings_template.py** to set up api and mysql credentials and initialize city variables*
9. > sudo apt install -y python3-pip
10. > cd klaviyo-weather-app
11. *install python3 virtual environment and packages using instructions below*
12. > sudo apt-get install python3-venv
13. > sudo apt install build-essential libssl-dev libffi-dev python-dev
14. > python3 -m venv env 
15. > source ./env/bin/activate
16. > pip3 install -r ~/klaviyo-weather-app/py3requirements.txt
17. *start the flask app subscription service send log messages to '/tmp/klaviyo-weather-app.subscription_service.log.$(date +\%Y\%m\%d)' using step 18*
18. > nohup python3 ~/klaviyo-weather-app/subscription_service.py > /tmp/klaviyo-weather-app.subscription_service.log.$(date +\%Y\%m\%d) &
19. *cron the daily weather api & email service and send log messages to '/tmp/klaviyo-weather-app.weather_api_email_service.log.$(date +\%Y\%m\%d)' by inserting cron entry in step 20 into your {{user}} account's crontab*
20.  > ###### 0 9 * * * /home/{{user}}/klaviyo-weather-app/env/bin/python3 /home/{{user}}/klaviyo-weather-app/weather_api_and_email_service.py > /tmp/klaviyo-weather-app.weather_api_and_email_service.log.$(date +\%Y\%m\%d) 2>&1

-----------------------------------------------------------------------------------------------------------------------------

## Scalability 
###### What happens if your app launches and goes viral? What bottlenecks would there be and how can you optimize the system or break through them?
>ANSWER: 

>Currently this web application is deployed using a shared CPU Ubuntu 18.04 LTS Digital Ocean droplet.  To control for high volume, the subscription page limits 50 requests per hour and 200 requests per day for each remote address.  If the app reaches resource limits due to to high traffic, optimizations include (but are not limited to):

>(a) upgrading the number of virtual CPUs (units of processing power) and RAM memory

>(c) switching from shared CPU to dedicated CPUs and consider to increase CPU and memory capacity and minimize hyperthread data loss

>(c) hosting the web application on a WGSI server or a more production-ready Django web application framework (Flask is a development server that doesn't efficiently handle many concurrent requests/threads)

>(d) separating the web application subscription server from the server(s) for the weather api and the weather email services

>(e) purging subscriptions a period of time after the sign up date such that users would have to sign up again to continue receiving emails for a particular city

>(f) consider distributing the compute/storage for city subscriptions with a high skew so the server load is more balanced



## Security 
###### How does your app handle invalid or even malicious input from users?
>ANSWER: 

>The subscription page checks for the validity of the email and limits the number of requests per remote address (50/hour and 200/day).  For edge cases not considered, please check the log file in /tmp/klaviyo-weather-app.subscription_service.log.$(date +\%Y\%m\%d)

## Re-Usability 
###### What components of your app would make sense to be their own modules or services so they can be re-used by other sections of code later?
>ANSWER: 

>The weather powered email is comprised of 3 main components: 

>1st component: the subscription app service (renders the html and validates/limits requests)  

>2nd component: the weather api service (loads MySql table tblFactCityWeather)

>3rd component: the weather email service (sends email based on stats in MySql table tblFactCityWeather)

If the utilized Ubuntu 18.04 LTS server was upgraded to have >=4 gb ram, a task scheduler service like airflow (https://airflow.apache.org/) could be useful to track and log the 2nd and 3rd app components (weather api and email service, respectively) as their own operator tasks within a DAG.  The airflow webserver can then be started to log, track, and visualize task failures as well as task durations in an intuitive manner.  To increase the power and robustness of the airflow task orchestration system, would consider changing from the local executor to the celery executor to isolate task processes from those populating the airflow scheduler and webserver.

## Re-Inventing the Wheel? 
###### We're big believers in not building what's already been built. Of course there are trade offs, so how did you decide whether to build functionality yourself or use existing solutions to make your job easier?
>ANSWER: 

>I believe using mature open-source package solutions with a large number of contributors should be utilized as much as possible since it has the benefit of being thoroughly tested by a smart community and furthers open-source package development.  However, building functionality yourself can be beneficial if:

>(a) more flexibility is needed than an open-source project currently allows 

>(b) hard drive or memory constraints with an open-source project that may be overkill/costly for the initial prototype

>(c) time is critical & the language(s) and/or abstraction layer(s) are unfamiliar or complex

The current weather app is built using Flask, a popular open-source microframework for creating flexible and lightweight web applications.  Instead of reinventing the wheel (or my own logic), I opted to use a popular python3 package for validating email addresses (https://pypi.org/project/py3-validate-email/) with added functionality such as domain validation and blacklist exclusion.


## Usability 
###### It's important that Klaviyo be easy to use — both for our users and the people they're emailing. How could your app be easier (or maybe more fun) to use?

>ANSWER:

>I believe the app could be easier & more intuitive to use by allowing users to specify what frequency (default is daily) and what local time they prefer to receive the weather powered email.  Currently, the emails are sent according to a daily cron schedule not based on local time.  The app should also have added functionality to allow email-city combinations to be unsubscribed from the weather powered email service.

>I believe the weather powered email could be more fun/engaging to the subscribed users by displaying interesting tidbits of weather data historically for the subscriber's city as well as some stats of the other 99 US cities.  For example, 5% of the other 99 populous US cities also experienced precipitation today.
