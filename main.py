from MSALATPersistence import MSALTokenHandler
from msal import PublicClientApplication
import logging
import json
import jwt
import requests
import urllib.parse
import base64
# App/Client ID: 9806a116-6f7d-4154-a06e-0c887dd51eed
# Tenant ID: 42a7cc42-d023-4e93-898d-3777ba423ebe

ONE_DRIVE_ENDPOINT = 'https://graph.microsoft.com/v1.0/me/drive'
  

def delta_query(token):
    api_headers = {
    "Authorization": f"bearer {token}",
    "Accept": "application/json"
    }
    response = requests.get(ONE_DRIVE_ENDPOINT + '/root/delta', headers=api_headers)
    json_response = json.dumps(response.json(), indent=2)
    print(json_response)  


def get_token():
    logging.basicConfig(level=logging.ERROR)
    token_handler = MSALTokenHandler('OneDriveSync',
                            client_id='9806a116-6f7d-4154-a06e-0c887dd51eed', 
                            authority='https://login.microsoftonline.com/consumers',
                            scopes=['Files.Read', 'User.Read'],
                            db_filepath='./accounts.db')
    return token_handler.get_token()

def main():
    token = get_token()
    delta_query(token)

if __name__ == '__main__':
    main()


    #jwt.decode(t, "secret", algorithms=["HS256"])

# auth_token_string = "Bearer "+token
# api_headers = {
#     "Authorization": auth_token_string,
#     "x-api-key": "randomjazz",
#     "Accept": "application/json"
# }

# print(api_headers)
# result = requests.get(api_call_url, headers=api_headers)
# result_json = result.json()
# something = result.text
# print(something)
