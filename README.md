# TECHIN-510-lab5
This repo is about Data Visualization. The features are:
1. Scrapering seattle local activitie infomation from the website;
2. Generating Longitude and latitude;
3. Scrapering weather infomation based on the Lon and Lat infomation;
4. Visualize the activity features in the Web App;
5. The visualation data in the Web App can update automatically since it stems from the Azure PostgreSQL database;
6. Also, the PostgreSQL management tool DBevaer is used as PC local checker.

## How to run
Type the commands below in your terminal:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
## What is included
### As for scraper:
```db.py``` is used to link to the Azure PostgreSQL database.  

```env.sample``` shows the format of DB info, and the ```.env``` has the real DB info with hiding by the ```.gitigonre``` to protect info security.  

```scraper.py``` is the main python file to scrape settle activity info with
1. Title
2. Venue (Town hall Seattle..etc)
3. Location (downtown, west, university district)
4. Category (Music, Theatre, etc)
5. Date
6. Geolocation (longitude, latitude)
7. Weather condition (sunny, cloudy, rainy)
8. Temperature
    1. min
    2. max
    3. windchill (feels-like)

### As for Web App:
```app.py``` is used to trigger the interactive Web App with seattle activity data visualization.

### As for Data Visulazation Practice:
```dataviz.ipynb``` and ```eda.ipybn``` are about this goal.

## Lesson Learned
- Some certain characters within the DB_PASSWORD need to be represented differently to ensure readability. For instance, the "/" character in my password must be entered as "%2F".
- DBeaver serves as an effective tool for managing PostgreSQL, facilitating the inspection and review of data stored on Azure PostgreSQL via a local PC application.
- Implementing code to append volume to an already established form is crucial for adding new columns to the table, provided they do not already exist. The code set looks like:
    ```bash
    cur.execute('''
        ALTER TABLE events ADD COLUMN IF NOT EXISTS weather_condition TEXT;
        ALTER TABLE events ADD COLUMN IF NOT EXISTS temperature_min INT;
        ALTER TABLE events ADD COLUMN IF NOT EXISTS temperature_max INT;
        ALTER TABLE events ADD COLUMN IF NOT EXISTS windchill INT;
        ALTER TABLE events ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION;
        ALTER TABLE events ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION;
    ''')
    ```
- Use Control+C in termnial to quit from the streamlit running.

## Questions
- How to parse raw weather data, filter and analyze weather conditions, maximum and minimum temperatures and wind chill index accurately? The weather related infomation in my database is currently very limited.
- In lab2, I save running time by using code to simultaneously fill longitude, latitude, as well as weather information for one same locations (Since different activities are held in on same location frequently) in the CSV file, avoiding repetitive API data retrievals. How can I incorporate this feature within the current coding logic in lab5?