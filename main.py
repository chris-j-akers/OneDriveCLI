from MSALATPersistence import MSALTokenHandler
from msal import PublicClientApplication
import logging
import json
import jwt
import requests
import urllib.parse
import base64
from datetime import datetime

# App/Client ID: 9806a116-6f7d-4154-a06e-0c887dd51eed
# Tenant ID: 42a7cc42-d023-4e93-898d-3777ba423ebe

ONE_DRIVE_ENDPOINT = 'https://graph.microsoft.com/v1.0/me/drive'
  

class OneDriveItem:

    def __init__(self, item_json):
        self.id = item_json['id']
        self.name = item_json['name']
        self.created_by = item_json['createdBy']['user']['displayName']
        self.last_modified_by = item_json['lastModifiedBy']['user']['displayName']
        self.created = datetime.fromisoformat(item_json['fileSystemInfo']['createdDateTime'])
        self.modified =datetime.fromisoformat(item_json['fileSystemInfo']['lastModifiedDateTime'])
        self.size = int(item_json['size'])
        self.type = 'd' if 'folder' in item_json else 'f'

    def __str__(self):
        #return f"{self.type} '{self.created_by}' '{self.last_modified_by}' {self.size} {str(self.created)} {str(self.modified)} {self.name}"
        return '{} {: >} {: >} {: >20} {: <}'.format(self.type, self.created_by, self.last_modified_by, self.size, self.name)

def delta_query(token):
    api_headers = {
    "Authorization": f"bearer {token}",
    "Accept": "application/json"
    }
    response = requests.get(ONE_DRIVE_ENDPOINT + '/root/delta', headers=api_headers)
    json_response = json.dumps(response.json(), indent=2)
 


def list_dir(token):
    api_headers = {
    "Authorization": f"bearer {token}",
    "Accept": "application/json"
    }
    response = requests.get(ONE_DRIVE_ENDPOINT + '/root/children', headers=api_headers)
    json_response = json.dumps(response.json(), indent=2)
    return [OneDriveItem(i) for i in response.json()['value']]


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
    items = list_dir(token)

    for item in items:
        print(f'{item}')


if __name__ == '__main__':
    #main()
    dt = datetime.fromisoformat("2023-08-03T10:57:19.417Z")

    # if path begins / then absolute path
    # else relative path, so add to cwd

    # Path is different for a cp, so for a cp we can make sure pop off the last
    # item and store it. Then replace it when done.

    path = 'root/chris/akers/is/skill'
    cdir = '../../wohoo' #root/chris/akers/wohoo

    s = cdir.split('/')
    p = path.split('/')
    print(s)
    print(p)
    for i in s:
        if i == '..':
            p.pop()
        else:
            p.append(i)
            
    print(p)
    print ('/'.join(p))


def parse_path(new_path):
    pass






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
