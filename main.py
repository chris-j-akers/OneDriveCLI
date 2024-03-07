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



def main():
    logging.basicConfig()
    #logging.getLogger().setLevel(logging.DEBUG)
    ods = OneDriveSynch()
    ods.initialise()
    ods.cd('/')
    print(ods.pwd())
    print(ods.ls())
    ods.cd('./health')
    print(ods.ls())
    ods.cd('../')
    print(ods.ls())
    ods.cd('jotterpad')
    print(ods.ls())
    ods.cd('Network Notes')
    print(ods.ls())
    ods.cd('../../')
    print(ods.ls())
    ods.cd('')
    print(ods.ls())
    ods.cd('./jotterpad/Network Notes')
    print(ods.ls())


if __name__ == '__main__':
    main()
 