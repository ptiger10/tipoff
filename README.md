# tipoff
**What is this?**

TipOff is a Python 3-based, Github-hosted, self-updating web app that identifies and profiles the location in California experiencing the most unusual weather activity every day.

For best viewing experience, open the .ipynb file on a desktop computer. To view on a mobile device, open the .html file.

**Technologies involved:**
- AWS EC2 instance running Amazon Linux (remote computing)
- Crontab (job scheduling)
- Open APIs hosted by NOAA (daily weather data)
- Pandas (data transformation and aggregation)
- Requests (API GET requests)
- Seaborn (visualization)
- Jupyter (interactive development and end-user accessibility)
- Github (repo hosting)

**How it works:**

The WeatherComputron (["Computron"](https://tv.avclub.com/the-office-the-banker-1798164192)) script runs every morning, collecting temperature data from over 600 NOAA weather stations in California. In order to maximize data coverage, the day analyzed (the "reference date") is the date 30 days prior to the current date.

For each station, Computron compares the mean temperature on the reference date with the average mean temperature at that station on that same day for the past 50 years. So if the reference date is January 1, 2017, Computron will fetch the max and min temperature at that same station on Jan 1, 2016, Jan 1, 2015,... all the way back to Jan 1, 1967.

For every station, Computron computes the absolute z-score as follows:

absolute value(_current mean station temp_ - _historical mean station temp_) /
 _standard deviation of historical temps at that station_

Once it has compiled a list of z-scores for a given reference date, Computron identifies the location with the most unusual weather activity.

The Dashboard notebook (CA Climate Dashboard.ipynb) displays the results of this analysis.

**How to try it for yourself:**
1. Clone the repo.
2. Register for an API token at https://www.ncdc.noaa.gov/cdo-web/token and replace the token reference in the headers section of the NOAA_API class.
3. Within a Jupyter notebook, import WeatherComputron.
4. Instantiate a member of the Temp_API subclass (e.g., resource = Temp_API('data', locationid='FIPS:06', startdate='2017-01-01', enddate='2017-01-01')). The keywords that you passed as arguments will appear as attributes on your new instance (e.g., Temp_API.startdate -> '2017-01-01').
5. Execute the fetch_page method on your class instance (i.e., Temp_API.fetch_page()). This will return a raw json result of all the indicators tracked in the GHCND dataset (including temperature, wind, and precipitation data) for all stations in California on January 1, 2017.
6. Experiment with other methods available to your instance. To discover all the methods available to a Temp_API instance, inspect the class definition and NOAA_API parent definition in WeatherComputron.py. Note: many of these methods set attributes on an instance itself (e.g., Temp_API.output). The purpose of writing output data directly to an attribute is to make it easier to reference this data at any time during your analytic process without requiring a redundant method call.
