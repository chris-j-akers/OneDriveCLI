from msal import PublicClientApplication
import sqlite3
import logging

logger = logging.getLogger(__name__)

class MSALTokenHandler:
    
    def __init__(self, app_name, client_id, authority, scopes=['User.Read'], db_filepath='./tokens') -> None:
        self._logger = logger.getChild(__class__.__name__)
        self._app_name = app_name
        self._scopes = scopes
        self._account = ''
        self._pca = PublicClientApplication(client_id=client_id, authority=authority, client_credential=None)
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

    def get_token(self):
        """
        Retrieves a new token using the PublicClientApplication class from MSAL.

        Attempts are made in the following order:

        1. Silently, using the MSAL built-in token cache
        2. Using a refresh token loaded from the Sqlite DB
        3. Interactively - Assumes a default browser is set

        Once a token is retrieved, its associated refresh token is persisted to
        the Sqlite DB for future use. Subsequent attempts will always try this
        token if the MSAL cache is empty, avoiding the need to re-authenticate.
        """
        self._logger.debug('get_token() called, running waterfall')

        # MSAL Cache
        if self._pca.get_accounts() != []:
            account = self._pca.get_accounts()[0]
            self._logger.debug(f'Found cached account for {account['username']}, acquiring silently')    
            token_data = self._pca.acquire_token_silent(account=self._pca.get_accounts()[0], scopes=self._scopes)
            if 'error' not in token_data:
                # There is no refresh token sent back with this one as it's the same as the previous token, anyway
                return token_data['access_token']

        # Refresh Tokee
        refresh_token = self._get_refresh_token_from_db()
        if refresh_token != '':
            self._logger.debug('trying refresh token')
            token_data = self._pca.acquire_token_by_refresh_token(refresh_token=refresh_token, scopes=self._scopes)
            if 'error' not in token_data:
                self._upsert_refresh_token_in_db(token_data['refresh_token'])
                return token_data['access_token']

        # Interactive
        token_data = self._pca.acquire_token_interactive(scopes=self._scopes)
        if 'error' not in token_data:
            self._upsert_refresh_token_in_db(token_data['refresh_token'])
            return token_data['access_token']

