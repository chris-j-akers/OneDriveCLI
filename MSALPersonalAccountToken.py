from msal import PublicClientApplication
import os
import sqlite3
import logging

logger = logging.getLogger(__name__)

class MSALPersonalAccountToken:
    
    def __init__(self, app_name, client_id, authority, scopes=['User.Read'], refresh_token='') -> None:
        self._logger = logger.getChild(__class__.__name__)
        self._app_name = app_name
        
        self._scopes = scopes
        self._current_token = ''
        self._refresh_token = refresh_token
        self._account = ''

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
        self._logger.debug('Created token table')

    def _set_refresh_token_from_db(self):
        cursor = self._connection.cursor()
        rows = cursor.execute('SELECT refresh_token FROM token where app_name = ?', (self._app_name,)).fetchall()
        if len(rows) == 0:
            self._logger.debug('No refresh_tokens found in token_db, setting to None')
            self._refresh_token = ''
        else:
            self._refresh_token = rows[0][0]
            self._logger.debug(f'Refresh token found in db')

    def _upsert_refresh_token_in_db(self):
        self._logger.debug('Updating refresh token in token_db')
        cursor = self._connection.cursor()
        cursor.execute('INSERT INTO token (app_name, refresh_token) VALUES (?, ?) ON CONFLICT (app_name) DO UPDATE SET refresh_token = ?;', (self._app_name, self._refresh_token, self._refresh_token))

    def _update_token_by_cache(self):
        if self._pca.get_accounts() == []:
            return False
        account = self._pca.get_accounts()[0]
        self._logger.debug(f'Found cached account for {account['username']}, using it to acquire token silently')    
        token_data = self._pca.acquire_token_silent(account=self._pca.get_accounts()[0], scopes=self._scopes)
        if not 'error' in token_data:
            self._current_token = token_data['access_token']
            self._upsert_refresh_token_in_db()
            return True
        return False

    def _update_token_by_refresh(self):
        if self._refresh_token == '':
            return False
        self._logger.debug('Refresh token available, using it to acquire token')
        token_data = self._pca.acquire_token_by_refresh_token(refresh_token=self._refresh_token, scopes=self._scopes)
        if not 'error' in token_data:
            self._current_token = token_data['access_token']
            self._refresh_token = token_data['refresh_token']
            self._upsert_refresh_token_in_db()
            return True
        return False

    def _update_token_interactive(self):
        token_data = self._pca.acquire_token_interactive(scopes=self._scopes)
        if not 'error' in token_data:
            self._current_token = token_data['access_token']
            self._refresh_token = token_data['refresh_token']
            self._upsert_refresh_token_in_db()
            return token_data['access_token']

    def get_token(self):
        self._logger.debug('get_token() called, running waterfall')
        if self._update_token_by_cache():
            self._logger.debug('returning token from cache')
            return self._current_token

        if self._update_token_by_refresh():
            self._logger.debug('returning token from refresh token')
            return self._current_token

        self._logger.debug('having to request token interactively')
        self._update_token_interactive()
        return self._current_token

  


