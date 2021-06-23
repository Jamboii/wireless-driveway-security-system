# /usr/bin/env python
# Download the twilio-python library from twilio.com/docs/libraries/python
import os
from twilio.rest import Client

# Find these values at https://twilio.com/user/account
# To set up environmental variables, see http://twil.io/secure
account_sid = os.environ['**********']
auth_token = os.environ['**********']

client = Client(account_sid, auth_token)

message=client.messages\
    .create(
        to="**********",
        from_="**********",
        body="Hello there!")
print(message.sid)
