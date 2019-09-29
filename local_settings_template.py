# INSTRUCTIONS:
# Fill in 'xxx' credentials accordingly and rename file to local_settings.py

# weather api
OPENWEATHERMAP_AUTH = {
    'api_key': 'xxx',
}

# mysql credentials
MYSQL_AUTH = {
    'user': 'xxx',
    'password': 'xxx',
    'host': 'xxx',
}



###### DO NOT EDIT BELOW ########
city_dict = {'5128594': 'New York, New York', '3882428': 'Los Angeles, California', '4887398': 'Chicago, Illinois', \
             '2646507': 'Houston, Texas', '5308655': 'Phoenix, Arizona', '4560349': 'Philadelphia, Pennsylvania', \
             '4726206': 'San Antonio, Texas', '5391811': 'San Diego, California', '4684888': 'Dallas, Texas', \
             '5392171': 'San Jose, California', '4671654': 'Austin, Texas', '4160021': 'Jacksonville, Florida', \
             '4691930': 'Fort Worth, Texas', '4509177': 'Columbus, Ohio', '5391959': 'San Francisco, California', \
             '4460243': 'Charlotte, North Carolina', '4259418': 'Indianapolis, Indiana', '5809844': 'Seattle, Washington', \
             '5419384': 'Denver, Colorado', '4138106': 'Washington, District of Columbia', '4930956': 'Boston, Massachusetts', \
             '5520993': 'El Paso, Texas', '4990729': 'Detroit, Michigan', '4644585': 'Nashville, Tennessee', \
             '5746545': 'Portland, Oregon', '4641239': 'Memphis, Tennessee', '4544349': 'Oklahoma City, Oklahoma', \
             '5506956': 'Las Vegas, Nevada', '4299276': 'Louisville, Kentucky', '4347778': 'Baltimore, Maryland', \
             '5263045': 'Milwaukee, Wisconsin', '5454711': 'Albuquerque, New Mexico', '5318313': 'Tucson, Arizona', \
             '5350937': 'Fresno, California', '5304391': 'Mesa, Arizona', '5389489': 'Sacramento, California', \
             '4180439': 'Atlanta, Georgia', '4393217': 'Kansas City, Missouri', '5417598': 'Colorado Springs, Colorado', \
             '4164138': 'Miami, Florida', '4487042': 'Raleigh, North Carolina', '5074472': 'Omaha, Nebraska', \
             '5367929': 'Long Beach, California', '4791259': 'Virginia Beach, Virginia', '5378538': 'Oakland, California', \
             '5037649': 'Minneapolis, Minnesota', '4553433': 'Tulsa, Oklahoma', '4671240': 'Arlington, Texas', \
             '4174757': 'Tampa, Florida', '4335045': 'New Orleans, Louisiana', '4281730': 'Wichita, Kansas', \
             '5150529': 'Cleveland, Ohio', '5325738': 'Bakersfield, California', '5412347': 'Aurora, Colorado', \
             '5323810': 'Anaheim, California', '5856195': 'Honolulu, Hawaii', '5392900': 'Santa Ana, California', \
             '5387877': 'Riverside, California', '4683416': 'Corpus Christi, Texas', '4297983': 'Lexington, Kentucky', \
             '5399020': 'Stockton, California', '5505411': 'Henderson, Nevada', '5045360': 'Saint Paul, Minnesota', \
             '4407066': 'St. Louis, Missouri', '4508722': 'Cincinnati, Ohio', '5206379': 'Pittsburgh, Pennsylvania', \
             '4469146': 'Greensboro, North Carolina', '5879400': 'Anchorage, Alaska', '4719457': 'Plano, Texas', \
             '5072006': 'Lincoln, Nebraska', '4167147': 'Orlando, Florida', '5359777': 'Irvine, California', \
             '5101798': 'Newark, New Jersey', '5174035': 'Toledo, Ohio', '4464368': 'Durham, North Carolina', \
             '5336899': 'Chula Vista, California', '4920423': 'Fort Wayne, Indiana', '5099836': 'Jersey City, New Jersey', \
             '4171563': 'St. Petersburg, Florida', '4705349': 'Laredo, Texas', '5261457': 'Madison, Wisconsin', \
             '5289282': 'Chandler, Arizona', '5110629': 'Buffalo, New York', '5525577': 'Lubbock, Texas', \
             '5313457': 'Scottsdale, Arizona', '5511077': 'Reno, Nevada', '5295985': 'Glendale, Arizona', \
             '5295903': 'Gilbert, Arizona', '4499612': 'Winston-Salem, North Carolina', '5509403': 'North Las Vegas, Nevada', \
             '4776222': 'Norfolk, Virginia', '4752186': 'Chesapeake, Virginia', '4693003': 'Garland, Texas', \
             '4700168': 'Irving, Texas', '4158476': 'Hialeah, Florida', '5350734': 'Fremont, California', \
             '5586437': 'Boise, Idaho', '4781708': 'Richmond, Virginia', '4315588': 'Baton Rouge, Louisiana', \
             '5811696': 'Spokane, Washington'}

cityIDset = {int(x) for x in city_dict.keys()}
valid_city_set = {' : '.join([y,x]) for x,y in city_dict.items()}
