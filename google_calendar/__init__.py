import json
from calendar_base import _BaseCalendar, _CalendarItem
import requests
from dateutil.parser import parse
import datetime
import time


class GoogleCalendar(_BaseCalendar):
    def __init__(
            self,
            *a,
            getAccessTokenCallback=None,
            calendarName=None,
            debug=False,
            **k
    ):
        self._getAccessTokenCallback = getAccessTokenCallback
        self.calendarName = calendarName
        self.calendars = set()
        self._calendarID = None
        self._baseURL = 'https://www.googleapis.com/calendar/v3/'
        self._debug = debug
        self.session = requests.session()
        super().__init__(*a, **k)
        self._GetCalendarID()

    def print(self, *a, **k):
        if self._debug:
            print(*a, **k)

    def _DoRequest(self, *a, **k):
        self.print('_DoRequest(', a, k)
        if self._GetCalendarID() is None:
            raise PermissionError('Error resolving calendar ID "{}"'.format(self.calendarName))

        self.session.headers['Authorization'] = 'Bearer {}'.format(self._getAccessTokenCallback())
        self.session.headers['Accept'] = 'application/json'
        for key, val in self.session.headers.items():
            if 'Auth' in key:
                val = val[:15] + '...'

            self.print('header', key, '=', val)

        resp = self.session.request(*a, **k)
        return resp

    def _GetCalendarID(self, nextPageToken=None):
        self.print('_GetCalendarID(nextPageToken=', nextPageToken)

        if self._calendarID is None:
            url = self._baseURL + 'users/me/calendarList'.format(
                self._getAccessTokenCallback(),
            )
            if nextPageToken:
                # This will request the next page of results.
                # This happens when the account has access to many-many calendars
                url += '?pageToken={}'.format(nextPageToken)

            self.print('29 url=', url)
            resp = requests.get(
                url,
                headers={
                    'Authorization': 'Bearer {}'.format(self._getAccessTokenCallback())
                }
            )
            self._NewConnectionStatus('Connected' if resp.ok else 'Disconnected')
            try:
                self.print('_GetCalendarID resp=', json.dumps(resp.json(), indent=2))
            except Exception as e:
                self.print('Error 87:', e)

            for calendar in resp.json().get('items', []):
                calendarName = calendar.get('summary', None)

                self.calendars.add(calendarName)

                if calendarName == self.calendarName:
                    self._calendarID = calendar.get('id')
                    self.print('calendar ID found "{}"'.format(self._calendarID))
                    break

            npToken = resp.json().get('nextPageToken', None)
            self.print('npToken=', npToken)
            while self._calendarID is None and npToken is not None:
                self.print('len(items)=', len(resp.json().get('items')))
                return self._GetCalendarID(nextPageToken=npToken)

        return self._calendarID

    def UpdateCalendar(self, calendar=None, startDT=None, endDT=None):
        '''
        Subclasses should override this

        :param calendar: a particular calendar ( None means use the default calendar)
        :param startDT: only search for events after this date
        :param endDT: only search for events before this date
        :return:
        '''
        self.print('96 UpdateCalendar(', calendar, startDT, endDT)

        startDT = startDT or datetime.datetime.now() - datetime.timedelta(days=1)
        endDT = endDT or datetime.datetime.now() + datetime.timedelta(days=7)

        startStr = datetime.datetime.utcfromtimestamp(startDT.timestamp()).isoformat() + "-0000"
        endStr = datetime.datetime.utcfromtimestamp(endDT.timestamp()).isoformat() + "-0000"
        self.print('startStr=', startStr)
        self.print('endStr=', endStr)

        url = self._baseURL + 'calendars/{}/events?timeMax={}&timeMin={}&singleEvents=True'.format(
            self._GetCalendarID(),
            endStr,
            startStr
        )
        resp = self._DoRequest(
            method='get',
            url=url
        )
        self._NewConnectionStatus('Connected' if resp.ok else 'Disconnected')
        self.print('136 resp=', resp.text)

        theseCalendarItems = []
        for item in resp.json().get('items', []):
            self.print('140 item=', json.dumps(item, indent=2, sort_keys=True))

            start = datetime.datetime.fromisoformat(item['start']['dateTime'])
            start = datetime.datetime.fromtimestamp(start.timestamp())  # remove the timezone (assume local timezone)
            self.print('95 start=', start)

            end = datetime.datetime.fromisoformat(item['end']['dateTime'])
            end = datetime.datetime.fromtimestamp(end.timestamp())  # remove the timezone (assume local timezone)

            hasAttachments = 'attachments' in item.keys()

            event = _CalendarItem(
                startDT=datetime.datetime.fromtimestamp(start.timestamp()),
                endDT=datetime.datetime.fromtimestamp(end.timestamp()),
                data={
                    'ItemId': item.get('id'),
                    'Subject': item.get('summary'),
                    'OrganizerName': item['creator']['email'],
                    'HasAttachments': hasAttachments,
                    'attachments': item.get('attachments', []),
                },
                parentCalendar=self,
            )
            self.print('143 event=', event)
            theseCalendarItems.append(event)

        self.RegisterCalendarItems(
            calItems=theseCalendarItems,
            startDT=startDT,
            endDT=endDT,

        )

        return resp

    def CreateCalendarEvent(self, subject, body, startDT, endDT):
        print('134 CreateCalendarEvent(', subject, body, startDT, endDT)
        timezone = time.tzname[-1] if len(time.tzname) > 1 else time.tzname[0]
        print('timezone=', timezone)

        data = {
            "kind": "calendar#event",
            "summary": subject,  # meeting subject
            "description": body,  # meeting body
            "start": {
                # "dateTime": startDT.astimezone(datetime.timezone.utc).isoformat(),# doesnt work on python 3.5
                "dateTime": datetime.datetime.utcfromtimestamp(startDT.timestamp()).isoformat() + '+00:00',
            },
            "end": {
                # "dateTime": endDT.astimezone(datetime.timezone.utc).isoformat(),# doesnt work on python 3.5
                "dateTime": datetime.datetime.utcfromtimestamp(endDT.timestamp()).isoformat() + '+00:00',
            },
        }
        self.print('data=', data)

        resp = self._DoRequest(
            method='POST',
            url='https://www.googleapis.com/calendar/v3/calendars/{calendarID}/events'.format(
                calendarID=self._calendarID,
            ),
            json=data,
        )
        self.print('CreateCalendarEvent resp=', resp.text)

        if resp.ok:
            # save the calendar item into memory
            item = resp.json()
            start = datetime.datetime.fromisoformat(item['start']['dateTime'])
            # start is offset-aware
            start = datetime.datetime.fromtimestamp(start.timestamp())  # make naive

            end = datetime.datetime.fromisoformat(item['end']['dateTime'])
            end = datetime.datetime.fromtimestamp(end.timestamp())  # make naive

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
            self.print('event=', event)
            self.RegisterCalendarItems(
                calItems=[event],
                startDT=start,
                endDT=end,

            )
        return resp

    def __str__(self):
        return '<217 GoogleCalendar: RoomName={}, ConnectionStatus={}, debug={}>'.format(
            self.calendarName,
            self._connectionStatus,
            self._debug
        )


if __name__ == '__main__':
    from gs_oauth_tools import AuthManager
    import datetime
    import time
    import webbrowser

    MY_ID = '4105'

    authManager = AuthManager(googleJSONpath=r'C:\Users\gmiller\PycharmProjects\gs_oauth\google_test_creds.json')
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
        getAccessTokenCallback=user.GetAccessToken,
        debug=True,
    )

    google.NewCalendarItem = lambda _, event: print('NewCalendarItem', event)
    google.CalendarItemChanged = lambda _, event: print('CalendarItemChanged', event)
    google.CalendarItemDeleted = lambda _, event: print('CalendarItemDeleted', event)

    google.UpdateCalendar()

    if len(google.GetNowCalItems()) == 0:
        google.CreateCalendarEvent(
            subject=time.asctime(),
            body='body',
            startDT=datetime.datetime.now(),
            endDT=datetime.datetime.now() + datetime.timedelta(minutes=5),
        )

    while True:
        google.UpdateCalendar()
        time.sleep(10)
