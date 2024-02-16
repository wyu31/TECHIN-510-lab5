import re
import json
import datetime
from zoneinfo import ZoneInfo
import html

import requests

from db import get_db_conn

# Base URLs for geolocation and weather APIs
CORD_BASE_URL = "https://nominatim.openstreetmap.org/search.php"
WEATHER_BASE_URL = "https://api.weather.gov/points/"

URL = 'https://visitseattle.org/events/page/'
URL_LIST_FILE = './data/links.json'
URL_DETAIL_FILE = './data/data.json'

def get_geolocation(venue, location):
    params = {
        'q': f'{venue}, {location}',
        'format': 'json'
    }
    response = requests.get(CORD_BASE_URL, params=params)
    data = response.json()
    if data:
        lat = data[0]['lat']
        lon = data[0]['lon']
        return lat, lon
    else:
        return None, None

def get_weather(lat, lon):
    # Assuming the response structure allows direct extraction of desired data
    response = requests.get(f"{WEATHER_BASE_URL}{lat},{lon}")
    data = response.json()
    forecast_url = data['properties']['forecast']
    weather_response = requests.get(forecast_url)
    weather_data = weather_response.json()
    
    # Extracting detailed weather information
    detailed_forecast = weather_data['properties']['periods'][0]  # Assuming first period is desired
    weather_info = {
        'condition': detailed_forecast.get('shortForecast', 'Not available'),
        'temperature_min': detailed_forecast.get('temperature', 'Not available'),  # Assuming API provides this directly
        'temperature_max': detailed_forecast.get('temperature', 'Not available'),  # May need adjustment based on API
        'windchill': detailed_forecast.get('temperature', 'Not available')  # Placeholder, adjust based on actual API data
    }
    return weather_info

def list_links():
    res = requests.get(URL + '1/')
    last_page_no = int(re.findall(r'bpn-last-page-link"><a href=".+?/page/(\d+?)/.+" title="Navigate to last page">', res.text)[0])

    links = []
    for page_no in range(1, last_page_no + 1):
        res = requests.get(URL + str(page_no) + '/')
        links.extend(re.findall(r'<h3 class="event-title"><a href="(https://visitseattle.org/events/.+?/)" title=".+?">.+?</a></h3>', res.text))

    json.dump(links, open(URL_LIST_FILE, 'w'))

def get_detail_page():
    links = json.load(open(URL_LIST_FILE, 'r'))
    data = []
    for link in links:
        try:
            row = {}
            res = requests.get(link)
            row['title'] = html.unescape(re.findall(r'<h1 class="page-title" itemprop="headline">(.+?)</h1>', res.text)[0])
            datetime_venue = re.findall(r'<h4><span>.*?(\d{1,2}/\d{1,2}/\d{4})</span> \| <span>(.+?)</span></h4>', res.text)[0]
            row['date'] = datetime.datetime.strptime(datetime_venue[0], '%m/%d/%Y').replace(tzinfo=ZoneInfo('America/Los_Angeles')).isoformat()
            row['venue'] = datetime_venue[1].strip() # remove leading/trailing whitespaces
            metas = re.findall(r'<a href=".+?" class="button big medium black category">(.+?)</a>', res.text)
            row['category'] = html.unescape(metas[0])
            row['location'] = metas[1]
            lat, lon = get_geolocation(row['venue'], row['location'])
            row['latitude'] = lat
            row['longitude'] = lon

            data.append(row)
        except IndexError as e:
            print(f'Error: {e}')
            print(f'Link: {link}')
    json.dump(data, open(URL_DETAIL_FILE, 'w'))

def insert_to_pg():
    conn = get_db_conn()
    cur = conn.cursor()

    # First, ensure that the events table exists with all the necessary columns
    cur.execute('''
        CREATE TABLE IF NOT EXISTS events (
            url TEXT PRIMARY KEY,
            title TEXT,
            date TIMESTAMP WITH TIME ZONE,
            venue TEXT,
            category TEXT,
            location TEXT,
            weather_condition TEXT,
            temperature_min INT,
            temperature_max INT,
            windchill INT,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION
        );
    ''')

    # Then, add latitude and longitude columns to your table if they don't already exist
    cur.execute('''
        ALTER TABLE events ADD COLUMN IF NOT EXISTS weather_condition TEXT;
        ALTER TABLE events ADD COLUMN IF NOT EXISTS temperature_min INT;
        ALTER TABLE events ADD COLUMN IF NOT EXISTS temperature_max INT;
        ALTER TABLE events ADD COLUMN IF NOT EXISTS windchill INT;
        ALTER TABLE events ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION;
        ALTER TABLE events ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION;
    ''')

    # Now, read the collected event data and weather information
    urls = json.load(open(URL_LIST_FILE, 'r'))
    data = json.load(open(URL_DETAIL_FILE, 'r'))

    # Insert or update each event into the events table
    for url, row in zip(urls, data):
        q = '''
        INSERT INTO events (url, title, date, venue, category, location, weather_condition, temperature_min, temperature_max, windchill, latitude, longitude)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (url) DO UPDATE SET
            title = EXCLUDED.title,
            date = EXCLUDED.date,
            venue = EXCLUDED.venue,
            category = EXCLUDED.category,
            location = EXCLUDED.location,
            weather_condition = EXCLUDED.weather_condition,
            temperature_min = EXCLUDED.temperature_min,
            temperature_max = EXCLUDED.temperature_max,
            windchill = EXCLUDED.windchill,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude;
        '''
        cur.execute(q, (
            url, 
            row['title'], 
            row['date'], 
            row['venue'], 
            row['category'], 
            row['location'], 
            row.get('weather_condition', 'Not available'),
            row.get('temperature_min', None),
            row.get('temperature_max', None),
            row.get('windchill', None),
            row.get('latitude'),  # Assuming latitude is always present
            row.get('longitude')  # Assuming longitude is always present
        ))

    # Commit the changes to the database
    conn.commit()

    # Close the database connection
    cur.close()
    conn.close()

if __name__ == '__main__':
    list_links()
    get_detail_page()
    insert_to_pg()