import datetime
import time
import webbrowser

from oauth_tools import AuthManager

MY_ID = str(datetime.date.today())

authManager = AuthManager(
    googleJSONpath='directory_test_extron.json',
)

user = authManager.GetUserByID(MY_ID)
if user is None:
    d = authManager.CreateNewUser(MY_ID, authType='Google')
    webbrowser.open(d.get('verification_uri'))
    print('User Code=', d.get('user_code'))

while authManager.GetUserByID(MY_ID) is None:
    print('waiting')
    time.sleep(3)

print('user=', authManager.GetUserByID(MY_ID))

