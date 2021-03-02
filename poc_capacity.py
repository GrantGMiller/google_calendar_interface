'''
The "resource" capacity is stored in the "Directory API"
https://developers.google.com/admin-sdk/directory/v1/reference/resources/calendars

https://developers.google.com/admin-sdk/directory/v1/reference/resources/calendars/get
'''
import time

import requests

from oauth_tools import AuthManager

authManager = AuthManager(
    googleJSONpath=r'C:\Users\gmiller\PycharmProjects\google_calendar_tools\directory_test_extron.json'
)
MY_ID = '1234'
user = authManager.GetUserByID(ID=MY_ID)
print('user=', user)
if user is None:
    authManager.CreateNewUser(ID=MY_ID, authType='Google')

    while authManager.GetUserByID(ID=MY_ID) is None:
        time.sleep(3)
        print('waiting for auth')
        user = authManager.GetUserByID(ID=MY_ID)

customer = 'thirdpartysched.biz'
calendarResourceId = 'thirdpartysched.mygbiz.com_36363231383836322d333636@resource.calendar.google.com'
url = f'https://www.googleapis.com/admin/directory/v1/customer/{customer}/resources/calendars/{calendarResourceId}'

resp = requests.get(
    url,
    params={
        'access_token': user.GetAcessToken()
    }
)
print('resp=', resp.text)