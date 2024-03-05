import sqlite3
import logging
import requests
import json
from MSALATPersistence import MSALTokenHandler as TokenHandler

logger = logging.getLogger(__name__)
                           
class OneDriveSynch:

    ONEDRIVE_ENDPOINT = 'https://graph.microsoft.com/v1.0'
    CLIENT_ID='9806a116-6f7d-4154-a06e-0c887dd51eed'
    AUTHORITY='https://login.microsoftonline.com/consumers'
    SCOPES=['Files.Read.All']

# private:
    
    def __init__(self, settings_db='./settings.db') -> None:
        self._logger = logger.getChild(__class__.__name__)
        self._logger.debug('creating OneDriveSynch object')
        self._setup_db(settings_db)
        self._token_handler = TokenHandler(app_name='onedrive-synch', 
                                           client_id=self.CLIENT_ID, 
                                           authority=self.AUTHORITY, 
                                           scopes=self.SCOPES, 
                                           db_filepath=settings_db)
        
        # If this is a new db it will be None
        self._drive_id = self._get_setting('drive_id')
        self._initialised = True if self._drive_id is not None else False
        self._logger.debug(f'drive id set to "{self._drive_id}" (if this is "None" then DB is new and Initialise() needs to be run)')

    def _setup_db(self, settings_db):
        self._logger.debug('initialising settings database')
        self._settings_db = sqlite3.connect(settings_db)
        self._settings_db.autocommit = True
        cursor = self._settings_db.cursor()
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table" and name="settings"')
        if len(cursor.fetchall()) == 0:
            self._logger.debug('no "settings" table in db, creating')
            self._create_settings_db()
        cursor.close()
        return
    
    def _create_settings_db(self):
        cursor = self._settings_db.cursor()
        cursor.execute('CREATE TABLE settings (key TEXT, value TEXT, PRIMARY KEY (key))')
        self._logger.debug('created settings db')
        cursor.close()

    def _get_api_headers(self, token):
        return {"Authorization": f"bearer {token}", "Accept": "application/json"}

    def _upsert_setting(self, key, value):
        self._logger.debug(f'updating value "{key}" to "{value}" in settings db')
        cursor = self._settings_db.cursor()
        cursor.execute('INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT (key) DO UPDATE SET value = ?;', (key, value, value))
        cursor.close()

    def _get_setting(self, key):
        self._logger.debug(f'getting value for "{key}" from settings db')
        cursor = self._settings_db.cursor()
        result = cursor.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchall()
        return result[0][0] if cursor.rowcount > 0 else None
    
    def _is_initialised(self):
        if self._initialised == False:
            print('initialisation has not been run, please run "ods initialise" first')
            return False
        return True
            
    def _wrangle_relative_path(self, path):
        self._logger.debug(f"attempting to wrangle new path from '{path}'")
        cwd = self._cwd.split('/')
        nwd = [dir for dir in path.split('/') if dir not in ['.', '']]
        for dir in nwd:
            if dir == '..':
                cwd.pop()
            else:
                cwd.append(dir)
        self._logger.debug(f"new path is '{cwd}'")
        return cwd if len(cwd) == 1 else '/'.join(cwd)

# public:
    
    def initialise(self):
        self._logger.debug("initialising ods")
        token = self._token_handler.get_token()
        response = requests.get(f'{self.ONEDRIVE_ENDPOINT}/me/drive', headers=self._get_api_headers(token))
        json = response.json()
        if 'id' not in json:
            self._logger.error('could not get drive id from msft graph response')
            print("error! no drive id in response from msft graph, cannot initialise ods")
            return
        self._logger.debug('got drive id from MSFT Graph, inserting into Settings db')
        self._drive_id = json['id']
        self._upsert_setting('drive_id', self._drive_id)
        self._initialised = True
        self.cd('/')

    def cd(self, path):
        if not self._is_initialised():
            return
        self._logger.debug(f'attempting to change directory to "{path}"')
        if path == '/':
            self._cwd = f'/drives/{self._drive_id}/root:'
            self._upsert_setting('cwd', self._cwd)
            return
        if path[0] == '/':
            self._cwd = ''
            self._cwd = self._wrangle_relative_path(path)
            self._upsert_setting('cwd', self._cwd)
            return
        self._cwd = self._wrangle_relative_path(path)
        self._upsert_setting('cwd', self._cwd)

    def pwd(self):
        if not self._is_initialised():
            return
        return self._cwd
    
    def ls(self):
        # If we're at root, lop off the : and just add /children
        # If not, then work out path in-between and add :/children
        if not self._is_initialised():
            return
        response = requests.get('https://graph.microsoft.com/v1.0/drives/539FB3F9A5FE3189/root:/health:/children', headers=self._get_api_headers(self._token_handler.get_token()))
        print(f'{self.ONEDRIVE_ENDPOINT}{self._cwd}:/children')
        # response = requests.get(f'{self.ONEDRIVE_ENDPOINT}{self._cwd + "/children"}', 
        #                         headers=self._get_api_headers(self._token_handler.get_token()))
        # print(response)
        # json_response = json.dumps(response.json(), indent=2)
        # return json_response

    def get(remote_path, local_path):
        pass

    def put(local_path, remote_path):
        pass