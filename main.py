import datetime
import json
import time
import webbrowser

from Extron.Scheduler.GoogleCalendar import GoogleCalendar
from oauth_tools import AuthManager

CALENDAR_NAME = 'Grants Test New Calendar'
JSON_PATH = 'calender_key.json'
MY_ID = '4105'

authManger = AuthManager(googleJSONpath=JSON_PATH)

user = authManger.GetUserByID(MY_ID)
if user is None:
    d = authManger.CreateNewUser(MY_ID, 'Google')
    time.sleep(1)
    print('d=', d)
    webbrowser.open(d['verification_uri'])
    print('User Code:\r\n', d['user_code'])

while user is None:
    user = authManger.GetUserByID(MY_ID)
    if user:
        break
    time.sleep(1)

data = authManger.GoogleData
print('data=', data)

google = GoogleCalendar(
    roomid='Grants Office',
    google_client_json={
        'client_id': data['client_id'],
        'client_secret': data['client_secret'],
        'refresh_token': user.RefreshToken,
    },
    utcOffsetSeconds=datetime.timedelta(hours=-5).total_seconds(),
    calendar_name=CALENDAR_NAME,
)

google._access_token = user.GetAcessToken()

google._updateCalendar(CALENDAR_NAME)
google._getCalendarID()

'''View current events'''
ret = []
google.GetEventsForStartAndEndDateTimes(
    startDate=datetime.date.today(),
    endDate=datetime.date.today() + datetime.timedelta(days=7),
    calendarEventList=ret,
)
for item in ret:
    print(item)

'''Create a new event'''

startDT = datetime.datetime.now()
endDT = startDT + datetime.timedelta(minutes=30)

newEvent = google.SetScheduledEvent(
    conf_room=CALENDAR_NAME,
    start=startDT,
    end=endDT,
)
google._setEvent(newEvent)
