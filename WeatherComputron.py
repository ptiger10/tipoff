
# coding: utf-8

# In[1]:

import requests
import json
import pandas as pd
import numpy as np
import datetime
import seaborn as sns


# In[2]:

import matplotlib
import matplotlib.pyplot as plt
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
get_ipython().magic('matplotlib inline')


# In[3]:

with open('.config') as fh:
    creds = json.loads(fh.read())


# In[10]:

class NOAA_API(object):
    '''Base class for API resources from NOAA, documentation at https://www.ncdc.noaa.gov/cdo-web/webservices/v2
    attributes:
    ----------
    baseurl (str): Climate Data Online endpoint published by NOAA
    headers (dict): authorization token passed in every API request, registered at https://www.ncdc.noaa.gov/cdo-web/token
    params (dict): parameters for API request (all key-value pairs must be strings)
        - startdate: accepts ISO format (YYYY-MM-DD) or date time (YYYY-MM-DDThh:mm:ss); limited to one year range
        - enddate: accepts ISO format (YYYY-MM-DD) or date time (YYYY-MM-DDThh:mm:ss); limited to one year range
        - limit: max of 1000 per request
        - offset: number of first resource in returned object; counting starts at 1; defaults to 25
        - datasetid: the container of all CDO data
            - GHCND: Global Historical Climatology Network Daily Summary
        - datatypeid: data label
            - TAVG -> average temperature recorded on given day **seems to be available only after mid-2015**
            - TMAX -> max temperature recorded on given day
            - TMIX -> min temperature recorded on given day
        - stationid: the source of most CDO data; the smallest granual of location data
            - #https://www.ncdc.noaa.gov/homr/reports for master list of stations
        - locationid: a specific latitude/longitude point such as a station, or a label representing a bounding area
            - FIPS -> state references between 01 - 51
            - FIPS:06 -> California
            - FIPS:US -> the United States
        - locationcategoryid: returns info on all locations under the supplied label
            - Available only on locationid resource
            - ST -> State; ZIP -> Zip Code; CITY -> City; CNTRY -> Country; CNTY - County
        - units: data will be scaled and converted to the specified units
            - metric -> celsisus and metric units
            - standard -> fahrenheit and non-metric units


    '''
    headers = {'token':creds['NOAA_token']}
    baseurl = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/'
    param_fields = [
        'startdate', 'enddate',
        'limit', 'offset',
        'datasetid', 'datatypeid',
        'stationid', 'locationid', 'locationcategoryid',
        'units']
    output = {}

    def __init__(self, resource, **kwargs):
        self.resource = resource
        self.today = datetime.datetime.today()

        for arg in kwargs:
            setattr(self, arg, kwargs[arg])

        self.set_params()
        self.original_params = self.params

    def set_params(self):
        '''Change the dictionary linked to the self.params object'''
        param_values = {}
        for parameter in self.param_fields:
            if hasattr(self, parameter):
                param_values[parameter] = getattr(self, parameter)
            else:
                continue
        self.params = param_values

    def reset_params(self):
        for parameter in self.param_fields:
            if parameter in self.original_params:
                setattr(self, parameter, self.original_params[parameter])
            else:
                try:
                    delattr(self, parameter)
                except:
                    continue
        self.set_params()

    def fetch_page(self, print_json=True):
        '''Fetch data from URL endpoint with requests library; print_json for raw inspection'''

        if not hasattr(self, 'params'):
            self.set_params()
        url = self.baseurl + self.resource + '?'

        request_string = requests.Request('GET', url=url, params=self.params).prepare().url
#         print('Fetching query at endpoint {}'.format(request_string))
        response = requests.get(url=url, params=self.params, headers=self.headers)

        if print_json:
            return response.json()
        else:
            return response

    def fetch_page_into_df(self):
        '''Returns spreadsheet of results (up to first 1000)'''

        response = self.fetch_page(print_json=False)
        try:
            df = pd.DataFrame(response.json()['results'])
        except KeyError:
            df = []
#         print('Success!') if len(df) > 0 else print('Failure...are all kw args spelled correctly?')
        return df

    def get_value_on_specific_date(self, date, datatype_id=None):
        '''params:
        ----------
        date (str): ISO format (YYYY-MM-DD)'''
        self.datatypeid = datatype_id

        self.startdate = date; self.enddate = date
        self.set_params()
        value = self.fetch_page_into_df()
        return value

    def set_reference_date(self):
        # Dataset is too sparse to use most recent observation date, so setting reference date on on one-month delay
        reference_date = self.today - datetime.timedelta(days=30)
        setattr(self, 'reference_date', reference_date.date())

    def compare_date_in_prior_years(self, start_year, datatype_id=None):
        if not hasattr(self, 'reference_date'):
            self.set_reference_date()

        current_date = self.reference_date
        year_range = range(int(start_year), int(current_date.year))
        comparisons = pd.DataFrame()
        for year in year_range:
            comparison_date = '{}-{}-{}'.format(str(year), current_date.strftime('%m'), current_date.strftime('%d'))
            comparison = self.get_value_on_specific_date(comparison_date, datatype_id)
            comparisons = pd.concat([comparisons, comparison])
        comparisons.set_index(['date','station'], inplace=True)
        return comparisons


# In[11]:

class Temp_API(NOAA_API):
    def __init__(self, resource, **kwargs):
        '''Historical temperature analysis tool using NOAA API
        params:
        ------
        datasetid (str): GHCND (Global Historical Climatology Network Daily Summary) dataset
        - #https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/readme.txt
        units (str): standard -> fahrenheit and non-metric units
        limit (str): 1000 -> API requests will return first 1000 results (max)
        '''

        self.datasetid = 'GHCND'
        self.units = 'standard'
        self.limit = '1000'
        super(Temp_API, self).__init__(resource, **kwargs)

    def compute_comparison_temp_statistics(self, start_year):
        min_comparisons = self.compare_date_in_prior_years(start_year, datatype_id='TMIN')
        max_comparisons = self.compare_date_in_prior_years(start_year, datatype_id='TMAX')
        average_temps = ((min_comparisons['value'] + max_comparisons['value']) / 2)
        average_temp_stats = average_temps.groupby('station').agg(['mean', 'std'])
        average_temp_stats.rename(columns={
            'mean': 'mean TAVG on {}'.format(self.reference_date.strftime('%m-%d')),
            'std': 'std TAVG on {}'.format(self.reference_date.strftime('%m-%d'))},
                                 inplace=True)

        self.output['comparison_min_temps'] = min_comparisons
        self.output['comparison_max_temps'] = max_comparisons
        self.output['comparison_avg_temps'] = average_temps
        return average_temp_stats

    def get_current_temps(self):
        '''returns:
        ----------
        current_average_temps (Series): average temperature values within location id on reference date
            - index: stationid'''
        if not hasattr(self, 'reference_date'):
            self.set_reference_date()

        min_temps = self.get_value_on_specific_date(self.reference_date, datatype_id='TMIN')
        max_temps = self.get_value_on_specific_date(self.reference_date, datatype_id='TMAX')
        min_temps.set_index(['station'], inplace=True)
        max_temps.set_index(['station'], inplace=True)
        current_average_temps = ((min_temps['value'] + max_temps['value']) / 2)
        current_average_temps.name = 'TAVG on {}'.format(self.reference_date.strftime('%m-%d'))

        self.output['current_min_temps'] = min_temps
        self.output['current_max_temps'] = max_temps
        self.output['current_avg_temps'] = current_average_temps
        return current_average_temps

    def build_comparison_plus_current_table(self, start_year, debug=False):
        current = self.get_current_temps()
        comparisons = self.compute_comparison_temp_statistics(start_year)

        joint_table = pd.concat((comparisons,current), axis=1)
        joint_table['diff_from_mean'] = (
            joint_table[current.name] - joint_table['mean TAVG on {}'.format(self.reference_date.strftime('%m-%d'))])
        joint_table['abs_diff_from_mean'] = abs(joint_table['diff_from_mean'])
        joint_table['abs_z-score'] = (
            joint_table['abs_diff_from_mean'] / joint_table['std TAVG on {}'.format(self.reference_date.strftime('%m-%d'))])
        joint_table.replace(np.inf, np.nan, inplace=True)
        self.reset_params()

        self.output['years_of_precedence'] = self.today.year - int(start_year)
        self.output['joint_table'] = joint_table
        self.output['unusual_station_stats'] = joint_table.loc[joint_table['abs_z-score'].argmax()]
        self.output['unusual_station_id'] = self.output['unusual_station_stats'].name
        if debug:
            return joint_table
        else:
            return self

    @staticmethod
    def get_station_info(stationid):
        headers = {'token':creds['NOAA_token']}
        url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/stations/{}'.format(stationid)
        response = requests.get(url=url, headers=headers)
        station_profile = response.json()
        return station_profile

    def analyze_joint_table(self):
        station_stats = self.output['unusual_station_stats']
        date = self.reference_date
        years_of_precedence = self.output['years_of_precedence']
        station_profile = self.get_station_info(self.output['unusual_station_id'])
        station_name = station_profile['name']
        station_name = station_name.split(', CA US')[0].title()
        temp = station_stats['TAVG on {}'.format(date.strftime('%m-%d'))]
        abnormality = int(round(station_stats['abs_z-score']))
        directionality = 'colder' if station_stats['diff_from_mean']<0 else 'hotter'
        historical_mean = station_stats.loc['mean TAVG on {}'.format(date.strftime('%m-%d'))]
        standard_deviation = station_stats.loc['std TAVG on {}'.format(date.strftime('%m-%d'))]

        result_narrative = '''
        The CA location with the most unusual weather on {} was:
        {} Station.
        The average temperature that day was {}°F, {} than usual.
        The temperature was {}x more unusual than the past {} years of historical precedent.

        Historical average temperature on this day at {} Station: {}°F
        Standard deviation: {}°F
        '''.format(date.strftime('%B %-d, %Y'),
                   station_name,
                   temp, directionality,
                   abnormality,years_of_precedence,
                   station_name, '{0:.2f}'.format(historical_mean),
                   '{0:.2f}'.format(standard_deviation))

        self.output['unusual_station_name'] = station_name
        self.output['result_narrative'] =  result_narrative
        return self


# In[18]:

def create_temp_resource(start_year, locationid):
    resource = Temp_API('data', locationid=locationid)
    resource.build_comparison_plus_current_table(start_year)
    return resource

def get_daily_result(start_year, locationid):
    resource = create_temp_resource(start_year, locationid)
    resource.analyze_joint_table()
    return resource


# In[19]:

def make_visualization(r):
    '''Make a visualization from an API resource after values have been fetched and processed'''
    min_line = r.output['comparison_min_temps'].xs(r.output['unusual_station_id'], level=1)
#     avg_line = r.output['comparison_avg_temps'].xs(r.output['unusual_station_id'], level=1).to_frame()
#     avg_line['datatype'] = 'TAVG'
    max_line = r.output['comparison_max_temps'].xs(r.output['unusual_station_id'], level=1)
#     df = pd.concat([max_line, avg_line, min_line])
    df = pd.concat([max_line, min_line])
    df['year'] = df.index.map(pd.to_datetime).year
    df.rename(columns={'value':'temp (°F)'}, inplace=True)

    sns.set_style('ticks')
    matplotlib.rcParams['font.family'] = 'DejaVu Sans'
    sns.lmplot('year', 'temp (°F)', data=df,
               hue='datatype', palette=dict(TMIN='b', TMAX='r'),
              fit_reg=True)
    plt.title('Temp at {} Station on prior {}s'.format(r.output['unusual_station_name'],
                                               r.reference_date.strftime('%B %-d')))




# In[39]:

def visualize_result(start_year='1986', locationid='FIPS:06', debug=False):
    resource = get_daily_result(start_year, locationid)
    make_visualization(resource)
    print(resource.output['result_narrative'])
    if debug:
        return resource


# In[58]:

# !jupyter nbconvert --to=python Weather.ipynb --output=WeatherComputron.py


# In[ ]:
