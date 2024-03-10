import sqlite3
import logging
import requests
import json
import os
from datetime import datetime
from MSALATPersistence import MSALTokenHandler as TokenHandler

logger = logging.getLogger(__name__)
                           
class OneDriveSynch:

    ONEDRIVE_ENDPOINT = 'https://graph.microsoft.com/v1.0'
    CLIENT_ID='9806a116-6f7d-4154-a06e-0c887dd51eed'
    AUTHORITY='https://login.microsoftonline.com/consumers'
    SCOPES=['Files.Read.All']

# private:
    
    def _dbg_print_json(self, json_data):
        # json_object = json.loads(json_data)
        json_formatted_str = json.dumps(json_data, indent=2)
        print(json_formatted_str)

    def __init__(self, settings_db='./settings.db') -> None:
        self._logger = logger.getChild(__class__.__name__)
        self._logger.debug('creating OneDriveSynch object')
        self._setup_db(settings_db)
        self._token_handler = TokenHandler(app_name='onedrive-synch', client_id=self.CLIENT_ID, authority=self.AUTHORITY, scopes=self.SCOPES, db_filepath=settings_db)
        if self._get_setting('is_initialised') == 'true':
            self._initialised = True
            self._drive_id = self._get_setting('drive_id')
            self._root = self._get_setting('root')
            self._cwd = self._get_setting('cwd')
            if self._get_setting('debug_on') == 'true':
                self.debug_on(True)
        else:
            self._initialised = False
            self._drive_id = None
            self._root = None
            self._cwd = None

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
        return result[0][0] if len(result) > 0 else None
       
    def _wrangle_relative_path(self, old_path, new_path):
        self._logger.debug(f"attempting to wrangle new path from '{old_path}' with relative path as {new_path}") 
        if new_path == '/':
            return new_path
        old = [path for path in old_path.split('/') if path not in ['','.']] if new_path[0] != '/' else []
        new = [path for path in new_path.split('/') if path not in ['','.']]
        for path in new:
            old.pop() if path == '..' else old.append(path)
        return '/' if old == [] else ('/' + '/'.join(old))

    def _get_api_headers(self, token):
        return {"Authorization": f"bearer {token}", "Accept": "application/json"}
    
    def _onedrive_api_get(self, url):
        self._logger.debug(f'sending get request to {url}')
        response = requests.get(self.ONEDRIVE_ENDPOINT + url, headers=self._get_api_headers(self._token_handler.get_token()))
        return response

# public:
    
    def debug_on(self, on):
        if on:
            logging.getLogger().setLevel(logging.DEBUG)
            self._upsert_setting('debug_on', 'true')
        else:
            logging.getLogger().setLevel(logging.ERROR)
            self._upsert_setting('debug_on', 'false')

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
        self._upsert_setting('root', self._root)
        self._cwd = '/'
        self._upsert_setting('cwd', self._cwd)
        self._upsert_setting('debug_on','false')
        self._initialised = True
        self._upsert_setting('is_initialised', 'true')
        self._logger.debug('initialisation complete')
        self.cd('/')

    def is_initialised(self):
        return self._initialised

    def cd(self, path):
        self._logger.debug(f'attempting to change directory to "{path}"')
        nwd = self._wrangle_relative_path(self._cwd, path)
        
        # Check path is valid
        root = self._root[:-1] if nwd == '/' else self._root
        response = self._onedrive_api_get(root + nwd)
        if 'error' in response.json():
            return f'error: invaid path ({self._root + nwd})'

        self._cwd = nwd
        self._upsert_setting('cwd', self._cwd)
        return self._root + self._cwd

    def pwd(self):
        return self._root + self._cwd

    def ls(self):
        time_fmt = '%Y-%m-%d %H:%M:%S'
        # If we're at root, lop off the : and just add /children
        url = self._root[:-1] + '/children' if self._cwd == '/' else self._root + self._cwd + ':/children'
        response = self._onedrive_api_get(url)
        json = response.json()
        if 'error' in json:
            return f'error: {json['error']['code']} | {json['error']['message']}'

        # Finangling required to get nice, justified output
        items = []
        field_lengths = {}
        field_lengths['type'] = 1
        self._download_url_cache = {}
        for item in json['value']:
            createdDateTime_str = datetime.strftime(datetime.fromisoformat(item['fileSystemInfo']['createdDateTime']), time_fmt)
            lastModifiedDateTime_str = datetime.strftime(datetime.fromisoformat(item['fileSystemInfo']['lastModifiedDateTime']), time_fmt)
            items.append(
                            {
                                'id': item['id'],
                                'createdBy' : item['createdBy']['user']['displayName'],
                                'createdDateTime' : createdDateTime_str,
                                'lastModifiedDateTime': lastModifiedDateTime_str,
                                'size': item['size'],
                                'lastModifiedBy': item['lastModifiedBy']['user']['displayName'],
                                'name': item['name'],
                                'type': 'd' if 'folder' in item else 'f',
                                'webUrl': item['webUrl'],
                            }
                        )
            
            field_lengths['id'] = max(len(item['id']), field_lengths.get(id, 0))
            field_lengths['createdBy'] = max(len(item['createdBy']['user']['displayName']), field_lengths.get('displayName',0))
            field_lengths['createdDateTime'] = max(len(createdDateTime_str), field_lengths.get('createdDateTime', 0))
            field_lengths['lastModifiedDateTime'] = max(len(lastModifiedDateTime_str), field_lengths.get('lastModifiedDateTime',0))
            field_lengths['size'] = max(len(str(item['size'])), field_lengths.get('size', 0))
            field_lengths['lastModifiedBy'] = max(len(item['lastModifiedBy']['user']['displayName']), field_lengths.get('displayName',0))
            field_lengths['name'] = max(len(item['name']), field_lengths.get('name',0))
            field_lengths['webUrl'] = max(len(item['webUrl']), field_lengths.get('webUrl',0))

        listing = ''
        for item in items:
            listing += ( 
                         f'{item['type']:<{field_lengths['type']+2}}'
                         f'{item['webUrl']:<{field_lengths['webUrl']+2}}'
                         f'{item['createdBy']:<{field_lengths['createdBy']+2}}'
                         f'{item['createdDateTime']:<{field_lengths['createdDateTime']+2}}'
                         f'{item['lastModifiedBy']:<{field_lengths['lastModifiedBy']+2}}'
                         f'{item['lastModifiedDateTime']:<{field_lengths['lastModifiedDateTime']}}'
                         f'{item['size']:>{field_lengths['size']+2}}'
                         f'  '
                         f'{item['name']:<{field_lengths['name']+2}}'
                         f'\n'
                       )
        listing += f'\n{self._root + self._cwd}\n'
        return listing

    def get(self, remote_filepath, local_path):
        self._logger.debug(f'attempting download of {remote_filepath} to {local_path}')

        remote_file = os.path.basename(remote_filepath)
        remote_path = os.path.dirname(remote_filepath)
        self._logger.debug(f'split path into [{remote_path}] / [{remote_file}]')

        remote_relative_path = self._cwd if remote_path == '' else self._wrangle_relative_path(self._cwd, remote_path)
        self._logger.debug(f'got filename: {remote_file} and path {remote_relative_path}')

        url = f'{self._root}/{remote_file}' if remote_relative_path == '/' else f'{self._root}{remote_relative_path}/{remote_file}'
        self._logger.debug(f'item url is {url}')

        response = self._onedrive_api_get(url)
        json = response.json()

        if 'error' in json:
            print(f'error: {json['error']['code']} | {json['error']['message']}')
            return

        download_url = json['@microsoft.graph.downloadUrl']
        self._logger.debug(f'item download url is: {download_url}')

        file_size = json['size']
        self._logger.debug(f'filesize is: {file_size}')

        print(f'Downloading {file_size} bytes ({remote_file})')
        response = requests.get(download_url)
        if response.status_code != 200:
            print(f'error: could not download file: status code: {response.status_code}')
            return
        
        open(local_path if not os.path.isdir(local_path) else f'{local_path}/{remote_file}', 'wb').write(response.content)
        self._logger.debug(f'file downloaded to {local_path}')

    def _get_item_id_for_put(self, local_file, remote_path):
        self._logger.debug(f'trying to get item id for "{local_file}" in "{remote_path}"')

        url = f'{self._root}/{local_file}' if remote_path == '/' else f'{self._root}{remote_path}/{local_file}'
        self._logger.debug(f'item url is {url}')

        response = self._onedrive_api_get(url)
        json = response.json()
        
        item_id = ''
        if 'error' in json:
            if json['error']['code'] == 'itemNotFound':
                self._logger.debug('file not found on one-drive, getting id of cwd instead')
                url = f'{self._root[:-1]}' if remote_path == '/' else f'{self._root}{remote_path}'
                response = self._onedrive_api_get(url)
                json = response.json()
                self._dbg_print_json(json)
                item_id = json['id']
                self._logger.debug(f'got directory item id {item_id} for upload')
            else:
                print(f'error: {json['error']['code']} | {json['error']['message']}')
                return ''
        else:
            item_id = json['id']
            self._logger.debug(f'file already exists, got item id: {item_id}')
        return item_id

    def put(self, local_filepath, rel_remote_path):
        self._logger.debug(f'attempting upload of {local_filepath} to {rel_remote_path}')

        local_file = os.path.basename(local_filepath)
        local_path = os.path.dirname(local_filepath)
        self._logger.debug(f'split local filepath into [{local_path}] / [{local_file}]')

        remote_path = self.cwd if rel_remote_path == '' else self._wrangle_relative_path(self._cwd, rel_remote_path)
        self._logger.debug(f'got upload path {remote_path}')
    
        item_id = self._get_item_id_for_put(local_file=local_file, remote_path=remote_path)
        if item_id == '':
            return

        print(f'item_id: {item_id}')


    def cat(self, local_path):
        pass