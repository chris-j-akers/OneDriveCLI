from MSALATPersistence import MSALTokenHandler
from msal import PublicClientApplication
import logging
import json
import jwt
import requests
# App/Client ID: 9806a116-6f7d-4154-a06e-0c887dd51eed
# Tenant ID: 42a7cc42-d023-4e93-898d-3777ba423ebe


def main():

    logging.basicConfig(level=logging.DEBUG)
    token_handler = MSALTokenHandler('OneDriveSync',
                                client_id='9806a116-6f7d-4154-a06e-0c887dd51eed', 
                                authority='https://login.microsoftonline.com/consumers',
                                scopes=['onedrive.readonly'],
                                db_filepath='./accounts.db')

    t = token_handler.get_token()
    json_formatted_str = json.dumps(t, indent=2)

    print(json_formatted_str)



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

    GRAPH_ENDPOINT = 'https://graph.microsoft.com/v1.0'
    ONE_DRIVE = '/me/drive'

    api_headers = {
        "Authorization": f"Bearer {t['access_token']}",
        "Accept": "application/json"
    }
    print(api_headers)
    r = requests.get(GRAPH_ENDPOINT + ONE_DRIVE, headers=api_headers)
    
    print(r.content)

if __name__ == '__main__':
    main()

