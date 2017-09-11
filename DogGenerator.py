import requests
import datetime

def generate_dog():
    '''Generate random dog image and time stamp
    returns
    -------
    img (Image): random dog image from open image API
    time (str): date and time stamp, formatted from datetime.now()'''
    
    response = requests.get('https://dog.ceo/api/breeds/image/random')
    img = response.json()['message']
    
    raw_time = datetime.datetime.now()
    formatted_time = datetime.datetime.strftime(raw_time, 'on %B %d, %Y at %-H:%M %p (UTC)')
    time = "This dog was generated {}".format(formatted_time)
    return img, time