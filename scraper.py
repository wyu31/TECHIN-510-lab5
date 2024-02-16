import re
import json
import datetime
from zoneinfo import ZoneInfo
import html
import time
import requests

from db import get_db_conn

URL = 'https://visitseattle.org/events/page/'
URL_LIST_FILE = './data/links.json'
URL_DETAIL_FILE = './data/data.json'
WEATHER_CACHE = {}
SLEEP_INTERVAL = 0.1

def list_links():
    res = requests.get(URL + '1/')
    last_page_no = int(re.findall(r'bpn-last-page-link"><a href=".+?/page/(\d+?)/.+" title="Navigate to last page">', res.text)[0])

    links = []
    for page_no in range(1, last_page_no + 1):
        res = requests.get(URL + str(page_no) + '/')
        links.extend(re.findall(r'<h3 class="event-title"><a href="(https://visitseattle.org/events/.+?/)" title=".+?">.+?</a></h3>', res.text))

    json.dump(links, open(URL_LIST_FILE, 'w'))

def get_geolocation(venue, location):
    cord_base_url = "https://nominatim.openstreetmap.org/search.php"
    try:
        # first try to find the location with the venue name
        query_params = {
            "q": venue + ", Seattle",
            "format": "jsonv2"
        }
        # specify headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Referer': 'https://nominatim.openstreetmap.org/ui/search.html'
        }
        res_cord = requests.get(cord_base_url, params=query_params, headers=headers)
        res_dict = res_cord.json()
        return (res_dict[0]['lat'], res_dict[0]['lon'])
    except:
        try: 
            # if not found, try to find location with location name
            query_params = {
                "q": location + ", Seattle",
                "format": "jsonv2"
            }
            # specify headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
                'Referer': 'https://nominatim.openstreetmap.org/ui/search.html'
            }
            res_cord = requests.get(cord_base_url, params=query_params, headers=headers)
            res_dict = res_cord.json()
            return (res_dict[0]['lat'], res_dict[0]['lon'])
        except:
            # if still not found, return None
            return (None, None)

def get_weather(geolocation, date):
    if geolocation is None:
        return None, None

    weather_base_url = "https://api.weather.gov/points/"
    try:
        res_weather = requests.get(f"{weather_base_url}{geolocation[0]},{geolocation[1]}")
        res_dict = res_weather.json()

        res_weather_detail = requests.get(res_dict['properties']['forecast'])
        forecast_data = res_weather_detail.json()

        formatted_date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%d')

        for period in forecast_data["properties"]["periods"]:
            period_start = datetime.datetime.strptime(period["startTime"], '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%d')
            if period_start == formatted_date:
                return period["detailedForecast"], period["temperature"]
    except Exception as ex:
        print('Exception in get_weather:', ex)
        
    return None, None

def get_detail_page():
    links = json.load(open(URL_LIST_FILE, 'r'))
    data = []
    for link in links:
        time.sleep(SLEEP_INTERVAL)  # Respectful scraping by waiting a bit between requests
        try:
            row = {}
            res = requests.get(link)
            # Extract necessary details here as per your page's HTML structure
            row['title'] = html.unescape(re.search(r'<h1 class="page-title">(.+?)</h1>', res.text).group(1))
            # Add other details extraction here...

            # Geolocation and weather data fetching
            geolocation = get_geolocation(row.get('venue', ''), row.get('location', ''))
            if geolocation != (None, None):
                weather_condition, temperature = get_weather(geolocation, row['date'])
                row.update({
                    'geolocation': geolocation,
                    'weather_condition': weather_condition,
                    'temperature': temperature
                })

            data.append(row)
        except Exception as e:
            print(f'Error processing {link}: {e}')
    
    json.dump(data, open(URL_DETAIL_FILE, 'w'))

def insert_to_pg():
    conn = get_db_conn()
    cur = conn.cursor()

    q = '''
    CREATE TABLE IF NOT EXISTS events (
        url TEXT PRIMARY KEY,
        title TEXT,
        date TIMESTAMP WITH TIME ZONE,
        venue TEXT,
        category TEXT,
        location TEXT,
        weather_condition TEXT,
        temperature_min TEXT,
        temperature_max TEXT,
        temperature_windchill TEXT
    );
    '''
    cur.execute(q)
    
    urls = json.load(open(URL_LIST_FILE, 'r'))
    data = json.load(open(URL_DETAIL_FILE, 'r'))
    for url, row in zip(urls, data):
        q = '''
        INSERT INTO events (url, title, date, venue, category, location, weather_condition, temperature_min, temperature_max, temperature_windchill)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (url) DO NOTHING;
        '''
        cur.execute(q, (
            url, 
            row['title'], 
            row['date'], 
            row['venue'], 
            row['category'], 
            row['location'], 
            row.get('weather_condition', None), 
            row.get('temperature_min', None), 
            row.get('temperature_max', None), 
            row.get('temperature_windchill', None)
        ))
    
    conn.commit()  # Commit the transaction
    cur.close()
    conn.close()

if __name__ == '__main__':
    list_links()
    get_detail_page()
    insert_to_pg()