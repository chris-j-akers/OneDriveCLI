from MSALATPersistence import MSALTokenHandler
from msal import PublicClientApplication
import logging
import shelve

# App/Client ID: 9806a116-6f7d-4154-a06e-0c887dd51eed
# Tenant ID: 42a7cc42-d023-4e93-898d-3777ba423ebe


logging.basicConfig(level=logging.DEBUG)
token = MSALTokenHandler('OneDriveSync',
                            client_id='9806a116-6f7d-4154-a06e-0c887dd51eed', 
                            authority='https://login.microsoftonline.com/consumers',
                            db_filepath='./accounts.db')


t = token.get_token()
print('=============================================================================')
print(t)
print('=============================================================================')
print('=============================================================================')
t2 = token.get_token()
print(t2)
print('=============================================================================')

