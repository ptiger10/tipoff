# tipoff
Created on September 18, 2017

The WeatherComputron.py script runs every morning, pulling in data from hundreds of NOAA weather stations in California. It compares the mean temperature of every station with the average mean temperature at that station on that day for the past 50 years. This difference is then weighted by the standard deviation of temperatures over that period (to produce a z-score, technically speaking). Computron then identifies the location with the most unusual weather in the state on that date.

The CA Climate Dashboard displays the results of this analysis.

