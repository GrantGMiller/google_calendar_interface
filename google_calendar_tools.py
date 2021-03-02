import json

from calendar_base import _BaseCalendar, _CalendarItem
import requests
from dateutil.parser import parse
import pytz


class GoogleCalendar(_BaseCalendar):
    def __init__(self, *a, getAccessTokenCallback=None, calendarName=None, **k):
        self._getAccessTokenCallback = getAccessTokenCallback
        self._calendarName = calendarName
        self._calendarID = None
        self._baseURL = 'https://www.googleapis.com/calendar/v3/'

        super().__init__(*a, **k)

    def _DoRequest(self, *a, **k):
        if self._getCalendarID() is None:
            raise PermissionError('No calendar ID')

        return requests.request(*a, **k)

    def _getCalendarID(self):
        if self._calendarID is None:
            url = self._baseURL + 'users/me/calendarList?access_token={0}'.format(
                self._getAccessTokenCallback(),
            )
            print('29 url=', url)
            resp = requests.get(url)
            print('_getCalendarID resp=', json.dumps(resp.json(), indent=2))
            for calendar in resp.json().get('items', []):
                if calendar.get('summary', None) == self._calendarName:
                    self._calendarID = calendar.get('id')
                    print('New calendar ID found "{}"'.format(self._calendarID))
                    break

        return self._calendarID

    def UpdateCalendar(self, calendar=None, startDT=None, endDT=None):
        '''
        Subclasses should override this

        :param calendar: a particular calendar ( None means use the default calendar)
        :param startDT: only search for events after this date
        :param endDT: only search for events before this date
        :return:
        '''
        print('UpdateCalendar(', calendar, startDT, endDT)
        startStr = startDT.replace(microsecond=0).isoformat() + "-0000"
        endStr = endDT.replace(microsecond=0).isoformat() + "-0000"
        url = self._baseURL + 'calendars/{}/events?access_token={}&timeMax={}&timeMin={}&singleEvents=True'.format(
            self._getCalendarID(),
            self._getAccessTokenCallback(),
            endStr,
            startStr
        )
        resp = self._DoRequest(
            method='get',
            url=url
        )
        # print('resp=', resp.text)

        theseCalendarItems = []
        for item in resp.json().get('items', []):
            # print('item=', json.dumps(item, indent=2, sort_keys=True))

            start = parse(item['start']['dateTime'])
            start = datetime.datetime.fromtimestamp(start.timestamp())

            end = parse(item['end']['dateTime'])
            end = datetime.datetime.fromtimestamp(end.timestamp())

            event = _CalendarItem(
                startDT=start,
                endDT=end,
                data={
                    'ItemId': item.get('id'),
                    'Subject': item.get('summary'),
                    'OrganizerName': item['creator']['email'],
                    'HasAttachment': False,
                },
                parentCalendar=self,
            )
            theseCalendarItems.append(event)

        self.RegisterCalendarItems(
            calItems=theseCalendarItems,
            startDT=startDT,
            endDT=endDT,

        )


if __name__ == '__main__':
    from oauth_tools import AuthManager
    import datetime
    import time
    import webbrowser

    MY_ID = '4105'

    authManager = AuthManager(googleJSONpath='calender_key.json')
    user = authManager.GetUserByID(MY_ID)

    if not user:
        d = authManager.CreateNewUser(MY_ID, 'Google')
        webbrowser.open(d.get('verification_uri'))
        print('d=', d)

        while not user:
            user = authManager.GetUserByID(MY_ID)
            time.sleep(1)

        print('user=', user)

    google = GoogleCalendar(
        calendarName='Grants Test New Calendar',
        getAccessTokenCallback=lambda: user.AccessToken
    )

    google.NewCalendarItem = lambda _, event: print('NewCalendarItem', event)
    google.CalendarItemChanged = lambda _, event: print('CalendarItemChanged', event)
    google.CalendarItemDeleted = lambda _, event: print('CalendarItemDeleted', event)

    while True:
        google.UpdateCalendar(
            startDT=datetime.datetime.utcnow(),
            endDT=datetime.datetime.utcnow() + datetime.timedelta(days=7),
        )
        time.sleep(10)
