from msal import PublicClientApplication
import os
import sqlite3
import logging

# App/Client ID: 9806a116-6f7d-4154-a06e-0c887dd51eed
# Tenant ID: 42a7cc42-d023-4e93-898d-3777ba423ebe

logger = logging.getLogger(f'{__name__}')
logging.basicConfig()

class MSALAccountToken:
    
    def __init__(self, app_name, client_id, authority, scopes=['User.Read'], refresh_token=None) -> None:
        self._logger = logger.getChild(__class__.__name__)
        self._app_name = app_name
        
        self._scopes = scopes
        self._current_token = None
        self._refresh_token = refresh_token

        self._pca = PublicClientApplication(client_id=client_id, authority=authority, client_credential=None)
        self._initialise_token_db()
        self._set_refresh_token_from_db()

    def _get_db_path(self):
        path = os.path.join(os.path.expanduser('~'), '.config', self._app_name)
        if not os.path.exists(path):
            self._logger.debug(f'token_db path not found, creating: {path}')
            os.mkdir(path)
        return os.path.join(path, self._app_name + '.db')

    def _initialise_token_db(self):
        self._logger.debug('Initialising token_db')
        db_path = self._get_db_path()
        self._connection = sqlite3.connect(db_path)
        self._connection.autocommit = True
        cursor = self._connection.cursor()
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="token"')
        if len(cursor.fetchall()) == 0:
            self._logger.debug('token table not found, creating')
            self._create_token_db()
            return
        self._logger.debug('token table found in db')

    def _create_token_db(self):
        cursor = self._connection.cursor()
        cursor.execute('CREATE TABLE token (app_name TEXT, refresh_token TEXT, PRIMARY KEY (app_name))')
        cursor.execute('INSERT INTO token VALUES (? , ?)', (self._app_name, None))
        self._logger.debug('Created token table')

    def _set_refresh_token_from_db(self):
        cursor = self._connection.cursor()
        rows = cursor.execute('SELECT refresh_token FROM token where app_name = ?', (self._app_name,)).fetchall()
        if len(rows) == 0:
            self._logger.debug('No refresh_tokens found in token_db, setting to None')
            self._refresh_token = None
        else:
            self._refresh_token = rows[0][0]
            self._logger.debug(f'Refresh token pulled from db is: {self._refresh_token}')

    def _upsert_refresh_token_in_db(self, refresh_token):
        self._logger.debug(f'Updating refresh token in token_db to: {refresh_token}')
        cursor = self._connection.cursor()
        cursor.execute('INSERT INTO token (app_name, refresh_token) VALUES (?, ?) ON CONFLICT (app_name) DO UPDATE SET refresh_token = ?;', (self._app_name, refresh_token, refresh_token))

logger.setLevel(logging.DEBUG)
token = MSALAccountToken('OneDriveSync',
                         client_id='9806a116-6f7d-4154-a06e-0c887dd51eed', 
                         authority='https://login.microsoftonline.com/consumers')

#token._upsert_refresh_token_in_db('BLAH')





#     def get_access_token_for_personal_account(self):
#         pca =  PublicClientApplication(client_id=self._client_id, 
#                                         authority=self._authority
#                                         scopes=self.scopes,
#                                         client_credential=None)
        
#         token_data = None
#         if pca.get_accounts() == []:
#             token_data = pca.acquire_token_interactive(scopes=scopes)
#         else:
#             token_data = pca.acquire_token_silent(scopes=scopes, account=pca.get_accounts()[0])

#         self.current_token = token_data['access_token']



# token_data = get_access_token_for_personal_account(client_id='9806a116-6f7d-4154-a06e-0c887dd51eed'

# print(token_data)


# print(result["access_token"])

# webbrowser.open('https://www.google.com')
