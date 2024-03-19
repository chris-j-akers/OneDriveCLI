from TinyAcceptorHTTPServer import TinyAcceptorHTTPServer
import sqlite3
import logging
import uuid
import json as jsonlib
import urllib
import webbrowser
import requests
from datetime import datetime as dt, timedelta
logger = logging.getLogger(__name__)

class MSALTokenHandler:
    
    ONEDRIVE_AUTHORISE_URL='https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize?'
    ONEDRIVE_TOKEN_SERVER_URL='https://login.live.com/oauth20_token.srf?'

    def _dbg_print_json(self, json_data):
        json_formatted_str = jsonlib.dumps(json_data, indent=2)
        print(json_formatted_str)

    def __init__(self, app_name, client_id, scopes=['User.Read'], db_filepath='./tokens.db') -> None:
        """
        Handles retrieving tokens from MSAL and persists the 
        associated refresh token to a `SqLite` db for future use.

        Args:
            `app_name` (`string`)   : Name of your application (used to pull the 
            token from storage, does not have to match the name in Azure)
            `client_id` (`string`)  : The app_id/client_id of your registered app 
            taken from the Azure portal
            `scopes` (`[string]`)   : List of scopes required, defaults to 'User.Read' (see [Azure documentation](https://learn.microsoft.com/en-us/graph/permissions-reference))
            `db_filepath` (`string`): The path and name of the `SQLite3` database 
            used to store refresh tokens (defaults to './tokens.db')

        Returns:
            `MSALTokenHandler`      : A new `MSALTokenHandler` object
        """
        self._logger = logger.getChild(__class__.__name__)
        self._app_name = app_name
        self._scopes = scopes
        self._account = ''
        self._client_id = client_id
        self._current_token = ''
        self._current_token_expiry = None
        self._initialise_token_db(db_filepath=db_filepath)

    def _initialise_token_db(self, db_filepath):
        self._logger.debug('Initialising token_db')
        self._connection = sqlite3.connect(db_filepath)
        self._connection.autocommit = True
        cursor = self._connection.cursor()
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="token"')
        if len(cursor.fetchall()) == 0:
            self._logger.debug('token table not found, creating')
            self._create_token_db()
            return
        self._logger.debug('token table found in db')
        cursor.close()

    def _create_token_db(self):
        cursor = self._connection.cursor()
        cursor.execute('CREATE TABLE token (app_name TEXT, refresh_token TEXT, PRIMARY KEY (app_name))')
        self._logger.debug('Created token table')
        cursor.close()

    def _get_refresh_token_from_db(self):
        cursor = self._connection.cursor()
        rows = cursor.execute('SELECT refresh_token FROM token where app_name = ?', (self._app_name,)).fetchall()
        if len(rows) == 0:
            self._logger.debug('No refresh_tokens found in token_db, setting empty')
            return ''
        else:
            self._logger.debug(f'Refresh token found in db')
            cursor.close()
            return rows[0][0]

    def _upsert_refresh_token_in_db(self, refresh_token):
        self._logger.debug('Updating refresh token in token_db')
        cursor = self._connection.cursor()
        cursor.execute('INSERT INTO token (app_name, refresh_token) VALUES (?, ?) ON CONFLICT (app_name) DO UPDATE SET refresh_token = ?;', (self._app_name, refresh_token, refresh_token))
        cursor.close()

    def _persist_token_data(self, token_data):
        self._current_token = token_data['access_token']
        self._current_id_token = token_data['id_token']
        self._current_token_expiry = dt.now() + timedelta(0,token_data['expires_in'])
        self._logger.debug(f'received token [{self._current_token}] from MSFT with expiry time in [{self._current_token_expiry.strftime("%Y-%m-%d %H:%M:%S")}]')
        refresh_token = token_data['refresh_token']
        self._upsert_refresh_token_in_db(refresh_token=refresh_token)
        self._logger.debug(f'set refresh token [{refresh_token}] in db.')

    def get_token_interactive(self):
        http_server = TinyAcceptorHTTPServer(port=0)
        state = str(uuid.uuid4())
        http_server.set_expected_state(state)
        params = {
                    "client_id": self._client_id,
                    "response_type": "code",
                    "redirect_uri": f"http://localhost:{http_server.get_port()}",
                    "response_mode": "query",
                    "scope": ' '.join(self._scopes),
                    "state": state
                }
        self._logger.debug(f'using params to request token: {params}')
        url = self.ONEDRIVE_AUTHORISE_URL + urllib.parse.urlencode(params)
        self._logger.debug(f'opening browser at: [{url}]')
        webbrowser.open(url)
        self._logger.debug(f'starting TinyAcceptorHTTPServer listening on port [{http_server.get_port()}]')
        http_server.wait_for_authorisation_code(timeout=300)
        auth_code = http_server.get_auth_code()
        if auth_code == '':
            self._logger.debug(f'no authorization code received from MSFT.')
            return False
        self._logger.debug(f'authorisation code [{auth_code}] received.')
        params = {
                    "client_id": self._client_id,
                    "redirect_uri": f"http://localhost:{http_server.get_port()}",
                    "code": auth_code,
                    "grant_type": "authorization_code"   
                 }
        self._logger.debug(f'requesting token from [{self.ONEDRIVE_TOKEN_SERVER_URL}]')
        response = requests.post(self.ONEDRIVE_TOKEN_SERVER_URL, headers={'Content-Type': 'application/x-www-form-urlencoded'}, data=urllib.parse.urlencode(params))       
        json = response.json()
        if 'error' in json:
            print(f'unable to get token, error from get_token_interactive():  {json["error"]} | {json["error_description"]}')
            return False
        self._persist_token_data(json)
        return True
    
    def get_token_refresh(self, refresh_token) -> str:
        params = {
                    "client_id": self._client_id,
                    "redirect_uri": f"http://localhost",
                    "refresh_token": refresh_token,
                    "scope": ' '.join(self._scopes),
                    "grant_type": "refresh_token"   
                 }
        self._logger.debug(f'requesting token from [{self.ONEDRIVE_TOKEN_SERVER_URL}]')
        params = urllib.parse.urlencode(params)
        self._logger.debug(f'with params: [{params}]')
        response = requests.post(self.ONEDRIVE_TOKEN_SERVER_URL, headers={'Content-Type': 'application/x-www-form-urlencoded'}, data=params)       
        json = response.json()
        if 'error' in json:
            print(f'unable to get token, error from get_token_refresh():  {json["error"]} | {json["error_description"]}')
            return False
        self._persist_token_data(json)
        return True
    
    def get_token(self):
        if self._current_token != '' and dt.now() < self._current_token_expiry:
            self._logger.debug('found token in cache, returning.')
            return self._current_token
        self._logger.debug('no valid cached token, checking for refresh token')       
        refresh_token = self._get_refresh_token_from_db()
        if refresh_token != '':
            self._logger.debug(f"got refresh token [{refresh_token}] from database")
            token = self.get_token_refresh(refresh_token)
            if token != '':
                return self._current_token
        self._logger.debug('no token in cache or refresh token available, getting interactively.')
        if self.get_token_interactive():
            return self._current_token
        
        self._logger.debug('unable to get a token from anywhere')
        print('error: unable to get a refresh token by any means, returning empty')
        return ''

