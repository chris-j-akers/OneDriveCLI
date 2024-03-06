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
    print(ods.pwd())
    ods.cd('health')
    print(ods.pwd())
    print(ods.ls())
    ods.cd('/tho-share')
    print(ods.ls())
    ods.cd('./jay_interview')
    print(ods.ls())
    ods.cd('../..')
    print("BALALAL")
    print(ods.pwd())
    print(ods.ls())
    ods.cd('./tech-books')
    print(ods.ls())
    # ods.cd('../')
    # print(ods.ls())


    s = "./hello"
    print(s[2:])
    print(s[:2])
if __name__ == '__main__':
    main()
 