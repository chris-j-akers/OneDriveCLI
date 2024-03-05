from MSALATPersistence import MSALTokenHandler
from msal import PublicClientApplication
import logging
import json
import jwt
import requests
import urllib.parse
import base64
from datetime import datetime
from OneDriveSynch import OneDriveSynch

# App/Client ID: 9806a116-6f7d-4154-a06e-0c887dd51eed
# Tenant ID: 42a7cc42-d023-4e93-898d-3777ba423ebe

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


def main():
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    ods = OneDriveSynch()
    ods.initialise()
    print(ods.pwd())
    ods.ls()


if __name__ == '__main__':
    main()
 