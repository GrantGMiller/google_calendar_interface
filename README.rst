An easy interface for Google Calendar

Install
=======
pip install google_calendar_interface

This project is a work in progress. Please excuse any unprofessionalism
=======================================================================

Example Usage
=============

::

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
