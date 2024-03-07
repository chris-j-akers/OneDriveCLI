import sqlite3
import logging
import requests
from datetime import datetime
from MSALATPersistence import MSALTokenHandler as TokenHandler

logger = logging.getLogger(__name__)
                           
class OneDriveSynch:

    ONEDRIVE_ENDPOINT = 'https://graph.microsoft.com/v1.0'
    CLIENT_ID='9806a116-6f7d-4154-a06e-0c887dd51eed'
    AUTHORITY='https://login.microsoftonline.com/consumers'
    SCOPES=['Files.Read.All']

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
            return '{} {: >} {: >} {: >10} {: <}'.format(self.type, self.created_by, self.last_modified_by, self.size, self.name)

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
        
        self._initialised = True if self._get_setting('is_initialised') == 'true' else False
        self._drive_id = self._get_setting('drive_id')
        self._root = self._get_setting('root')
        self._cwd = self._get_setting('cwd')
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
        self._upsert_setting('is_initialised', 'false')

    def _upsert_setting(self, key, value):
        self._logger.debug(f'updating value "{key}" to "{value}" in settings db')
        cursor = self._settings_db.cursor()
        cursor.execute('INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT (key) DO UPDATE SET value = ?;', (key, value, value))
        cursor.close()

    def _get_setting(self, key):
        self._logger.debug(f'getting value for "{key}" from settings db')
        cursor = self._settings_db.cursor()
        result = cursor.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchall()
        self._logger.debug(f'value is "{result[0][0]}"')
        return result[0][0] if len(result) > 0 else None
    
    def _is_initialised(self):
        if self._initialised == False:
            print('initialisation has not been run, please run "ods initialise" first')
            return False
        return True
    
    def _wrangle_relative_path(self, old_path, new_path):
        self._logger.debug(f"attempting to wrangle new path from '{old_path}' with relative path as {new_path}") 
        if new_path in ['/']:
            return new_path
        old = [path for path in old_path.split('/') if path not in ['','.']]
        new = [path for path in new_path.split('/') if path not in ['','.']]
        for path in new:
            old.pop() if path == '..' else old.append(path)
        return '/' if old == [] else '/' + '/'.join(old)

    def _get_api_headers(self, token):
        return {"Authorization": f"bearer {token}", "Accept": "application/json"}
    
    def _onedrive_api_get(self, url):
        self._logger.debug(f'sending get request to {url}')
        response = requests.get(self.ONEDRIVE_ENDPOINT + url, headers=self._get_api_headers(self._token_handler.get_token()))
        return response

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
        self._root = f'/drives/{self._drive_id}/root:'
        self._cwd = '/'
        self._upsert_setting('root', self._root)
        self._upsert_setting('cwd', self._cwd)
        self._initialised = True
        self._upsert_setting('is_initialised', 'true')
        self._logger.debug('initialisation complete')
        self.cd('/')

    def cd(self, path):
        self._logger.debug(f'attempting to change directory to "{path}"')
        self._cwd = self._wrangle_relative_path(self._cwd, path)
        self._upsert_setting('cwd', self._cwd)

    def pwd(self):
        return self._root + self._cwd
    
    def ls(self):
        # If we're at root, lop off the : and just add /children
        url = self._root[:-1] + '/children' if self._cwd == '/' else self._root + self._cwd + ':/children'
        response = self._onedrive_api_get(url)
        json = response.json()
        if 'error' in json:
            return f'error: {json['error']['code']} | {json['error']['message']}'
        items = []
        for item in  json['value']:
            items.append(self.OneDriveItem(item))
        return f'{url}\n' + ''.join([str(item) + '\n' for item in items])

    def get(remote_path, local_path):
        pass

    def put(local_path, remote_path):
        pass