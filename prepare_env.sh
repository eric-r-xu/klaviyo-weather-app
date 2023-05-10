#!/bin/sh
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install git
cd ~/
git clone https://github.com/eric-r-xu/klaviyo-weather-app.git
sudo apt install -y python3-pip
sudo apt-get install python3-setuptools
cd klaviyo-weather-app;sudo apt-get install python3-venv
sudo apt install build-essential libssl-dev libffi-dev python-dev-is-python3
python3 -m venv env
. ./env/bin/activate
python -m pip install --upgrade pip
sudo apt-get install libsasl2-dev libsasl2-2 libsasl2-modules-gssapi-mit
sudo apt-get install libmysqlclient-dev
pip install -r ~/klaviyo-weather-app/py3requirements.txt
python -m pip install git+https://gitea.ksol.io/karolyi/py3-validate-email@v1.0.9
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list
sudo apt-get update
sudo apt-get install redis
