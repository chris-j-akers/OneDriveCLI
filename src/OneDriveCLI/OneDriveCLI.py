import sqlite3
import logging
import requests
import json as jsonlib
import os
import sys
from datetime import datetime
if not (path := os.path.abspath(os.path.dirname(__file__))) in sys.path:
    sys.path.append(path)
from OneDriveTokenHandler.OneDriveTokenHandler import OneDriveTokenHandler

logger = logging.getLogger(__name__)
                           
class OneDriveCLI:

    ONEDRIVE_ENDPOINT = 'https://graph.microsoft.com/v1.0'
    CLIENT_ID='9806a116-6f7d-4154-a06e-0c887dd51eed'
    AUTHORITY='https://login.microsoftonline.com/consumers'
    SCOPES=['Files.ReadWrite.All', 'openid']

# private:
    
    def _dbg_print_json(self, json_data):
        json_formatted_str = jsonlib.dumps(json_data, indent=2)
        print(json_formatted_str)

    def __init__(self, settings_db='./settings.db') -> None:
        self._logger = logger.getChild(__class__.__name__)
        self._logger.debug('creating OneDriveSynch object')
        self._setup_db(settings_db)
        self._token_handler = OneDriveTokenHandler(app_name='onedrive-synch', client_id=self.CLIENT_ID, scopes=self.SCOPES, db_filepath=settings_db)
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
       
    def _get_absolute_path(self, old_path, new_path):
        self._logger.debug(f"attempting to wrangle new path from '{old_path}' based on relative path as {new_path}") 
        if new_path == '/':
            return new_path
        old = [path for path in old_path.split('/') if path not in ['','.']] if new_path[0] != '/' else []
        new = [path for path in new_path.split('/') if path not in ['','.']]
        for path in new:
            old.pop() if path == '..' else old.append(path)
        return '/' if old == [] else ('/' + '/'.join(old))

    def _get_default_api_headers(self, token):
        return {"Authorization": f"bearer {token}", "Accept": "application/json"}
    
    def _onedrive_api_get(self, url):
        self._logger.debug(f'sending get request to {url}')
        response = requests.get(self.ONEDRIVE_ENDPOINT + url, headers=self._get_default_api_headers(self._token_handler.get_token()))
        return response
    
    def _get_onedrive_item_id(self, remote_path):
        self._logger.debug(f'trying to get item id for "{remote_path}"')
        url = f'{self._root[:-1]}' if remote_path == '/' else f'{self._root}{remote_path}'
        response = self._onedrive_api_get(url)
        if 'error' in (json := response.json()):
            self._logger.debug(f'error returned from API (this is fine if problem is item doesn\'t exist): {json["error"]["code"]} | {json["error"]["message"]}')
            return ''
        return json['id']

    def _get_parent_item_id(self, remote_path):
        parent_dir_list = [path for path in remote_path.split('/') if path not in ['','.']]
        parent_dir_list.pop()
        parent_dir = '/' if parent_dir_list == [] else ('/' + '/'.join(parent_dir_list))
        return self._get_onedrive_item_id(parent_dir)

    def _put_item_exists(self, local_file, remote_path):
        self._logger.debug(f'trying to get item id for "{local_file}" in "{remote_path}"')
        url = f'{self._root}/{local_file}' if remote_path == '/' else f'{self._root}{remote_path}/{local_file}'
        self._logger.debug(f'item url is {url}')
        response = self._onedrive_api_get(url)
        if not 'error' in (response.json()):
            return True
        return False

    def _put_get_upload_session(self, local_file, remote_path):
        self._logger.debug(f'getting upload session for upload of {local_file} to {remote_path}')
        if (dir_id := self._get_onedrive_item_id(remote_path=remote_path)) == '':
            print(f'error: item: {remote_path} doesn\'t exist')
            return ''
        url = f'/drives/{self._drive_id}/items/{dir_id}:/{local_file}:/createUploadSession'
        self._logger.debug(f'using url: {url}')
        headers = self._get_default_api_headers(self._token_handler.get_token())
        headers['Content-Type'] = 'application/json'
        self._logger.debug(f'headers = {headers}')
        response = requests.post(self.ONEDRIVE_ENDPOINT + url, headers=headers, json='{ "item": { "@microsoft.graph.conflictBehavior": "replace" } }')
        if 'error' in (json := response.json()):
            print(f'error: {json['error']['code']} | {json['error']['message']}')
            return ''
        return json['uploadUrl']
    
    def _put_upload(self, local_filepath, upload_url):
        chunk_size = 10485760 # Must be divisible by 327,680, according to MSFT
        file_size = os.path.getsize(local_filepath)
        print(f'Uploading [{local_filepath}] ({file_size} bytes)',flush=True)
        chunk_start = 0
        chunk_end = 0
        with open(local_filepath, 'rb') as upload_file:
            while (bytes_read := upload_file.read(chunk_size)):
                self._logger.debug(f'bytes_read = {len(bytes_read)}')
                chunk_end = upload_file.tell()
                if (response := requests.put(upload_url, 
                                            bytes_read, 
                                            headers={"Accept": "application/json", 
                                                    "Content-Length": f"{file_size}", 
                                                    "Content-Range": f"bytes {chunk_start}-{chunk_end-1}/{file_size}"})).status_code not in [202, 201, 200]:
                    print(f'\nerror uploading file {local_filepath} with HTTP status code as {response.status_code} and response as {response.text}, partial upload you may need to delete manually')
                    self._logger.debug(f'error uploading at chunk start: {chunk_start}, chunk_end: {chunk_end}')
                    upload_file.close()
                    return
                print('.', end='', flush=True)
                chunk_start = upload_file.tell()
        print('Done')
        response = requests.delete(upload_url) # Clean up
        self._logger.debug(f'delete upload url response: {response.status_code}')

    def _download(self, url, filename, destination):
        chunk_size = 10485760
        print(f'Downloading [{filename}] to [{destination}]', flush=True)
        if (response := requests.get(url, stream=True)).status_code != 200:
            print(f'error: could not download file: status code: {response.status_code}')
            return
        with open(destination if not os.path.isdir(destination) else f'{destination}/{filename}', 'wb') as destination_file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                print('.', end='', flush=True)
                destination_file.write(chunk)
        print('Done')
        self._logger.debug(f'file downloaded to {destination}')
        pass

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
        response = self._onedrive_api_get('/me/drive')
        response = requests.get(f'{self.ONEDRIVE_ENDPOINT}/me/drive', headers=self._get_default_api_headers(token))
        if 'id' not in (json := response.json()):
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
        nwd = self._get_absolute_path(self._cwd, path)
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
        if 'error' in (json := response.json()):
            return f'error: {json['error']['code']} | {json['error']['message']}'
        # Now to get nice, justified outlook
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

    def get(self, rel_remote_filepath, local_path):
        self._logger.debug(f'attempting download of {rel_remote_filepath} to {local_path}')
        remote_file = os.path.basename(rel_remote_filepath)
        rel_remote_path = os.path.dirname(rel_remote_filepath)
        abs_remote_path = self._cwd if rel_remote_path == '' else self._get_absolute_path(self._cwd, rel_remote_path)
        url = f'{self._root}/{remote_file}' if abs_remote_path == '/' else f'{self._root}{abs_remote_path}/{remote_file}'
        response = self._onedrive_api_get(url)
        if 'error' in (json := response.json()):
            print(f'error: {json['error']['code']} | {json['error']['message']}')
            return
        self._download(json['@microsoft.graph.downloadUrl'], remote_file, local_path)

    def put(self, local_filepath, rel_remote_path, force=False):
        local_file = os.path.basename(local_filepath)
        remote_path = self.cwd if rel_remote_path == '' else self._get_absolute_path(self._cwd, rel_remote_path) 
        if force == False and self._put_item_exists(local_file=local_file, remote_path=remote_path):
            self._logger.debug('file found on one-drive, checking with user')
            if input(f'[{local_file}] already exists on OneDrive in [{remote_path}], do you want to replace? (Y/N): ').upper() == 'N':
                return ''
        if (upload_url := self._put_get_upload_session(local_file=local_file, remote_path=remote_path)) == '':
            return
        self._put_upload(local_filepath=local_filepath, upload_url=upload_url)
        
    def rm(self, rel_remote_path, force=False):
        abs_remote_path = self._get_absolute_path(self._cwd, rel_remote_path)
        self._logger.debug(f'attempting to remove item: {abs_remote_path}')
        if (item_id := self._get_onedrive_item_id(remote_path=abs_remote_path)) == '':
            print('error: item does not exist')
            return
        if input(f'Are you sure you want to move item {abs_remote_path} to the recycle bin? (Y/N)').upper() == 'N':
            return ''        
        url = f'/drives/{self._drive_id}/items/{item_id}'
        headers = self._get_default_api_headers(self._token_handler.get_token())
        response = requests.delete(self.ONEDRIVE_ENDPOINT + url, headers=headers)
        if response.status_code != 204:
            print(f'error: error occurred during deletion of item: {response.text}')
            return
        print(f'deleted: {abs_remote_path}')        

    def mkdir(self, rel_remote_path):
        abs_remote_path = self._get_absolute_path(self._cwd, rel_remote_path)
        self._logger.debug(f'attempting to mkdir path: {abs_remote_path}')
        if self._get_onedrive_item_id(remote_path=abs_remote_path) != '':
            print('error: directory already exists')
            return
        if (parent_item_id := self._get_parent_item_id(abs_remote_path)) == '':
            print('error: parent directory specified does not exist')
            return
        url = f'/drives/{self._drive_id}/items/{parent_item_id}/children'
        headers = self._get_default_api_headers(self._token_handler.get_token())
        headers['Content-Type'] = 'application/json'
        self._logger.debug(f'headers = {headers}')
        payload = (
                    {
                        "name": f"{rel_remote_path.split('/')[-1]}",
                        "folder": { },
                        "@microsoft.graph.conflictBehavior": "rename"
                    }
                  )
        response = requests.post(self.ONEDRIVE_ENDPOINT + url, headers=headers, json=payload)
        if response.status_code != 201:
            print(f'error: error occurred during creation of directory: {response.text}')
            return
        print(f'created: {abs_remote_path}')

    def cat(self, local_path):
        pass

def get_arg(arglist, index, default=None):
    try:
        return arglist[index]
    except(IndexError):
        return default

def main():
    logging.basicConfig()
    odc = OneDriveCLI(f'{os.path.expanduser('~')}/.config/OneDriveCLI/settings.db')

    if get_arg(sys.argv, 1) == None:
        print("----------------------------------------------------------------------------------------------")
        print("OneDriveCLI | (C) 2024 Chris Akers | https://github.com/chris-j-akers | https://blog.cakers.io")
        print("----------------------------------------------------------------------------------------------")
        print("initialise                      : 'odc init'")
        print("change directory                : 'odc cd <dir_name>'")
        print("list items in current directory : 'odc ls'")
        print("get current directory           : 'odc pwd'")
        print("make new directory              : 'odc mkdir <remote_path>'")
        print("delete item                     : 'odc rm <remote_path>'")
        print("get file from current directory : 'odc get <remote_path> [local_path]'")
        print("put file to current directory   : 'odc put <local_path> [remote_path]'")
        print("put file to current directory   : 'odc put <local_path> [remote_path]'")
        print("enable debug traces             : 'odc debug-on' ")
        print("disable debug traces            : 'odc debug-off' ")
        print("")
        print("* <> = required parameter, [] = optional parameter")
        print("----------------------------------------------------------------------------------------------")
        sys.exit(0)

    if sys.argv[1] == 'init':
        odc.initialise()
        sys.exit(0)

    if not odc.is_initialised():
        print('initialisation has not been run, please run "ods init" first')
        sys.exit(1)

    match(sys.argv[1]):
        case 'cd':
            path = get_arg(sys.argv, 2, '/')
            print(odc.cd(path))
        case 'ls':
            print(odc.ls())
        case 'pwd':
            print(odc.pwd())
        case 'get':
            if (source := get_arg(sys.argv,2)) is None:
                print("error: no source file specified")
                sys.exit(1)
            destination = get_arg(sys.argv, 3, './')
            odc.get(source, destination)
        case 'put':
            if (source := get_arg(sys.argv,2)) is None:
                print("error: no source file specified")
                sys.exit(1)
            destination = get_arg(sys.argv,3, './')
            odc.put(source, destination)
        case 'mkdir':
            if (path := get_arg(sys.argv, 2)) is None:
                print('error: no directory name specified')
                sys.exit(1)
            odc.mkdir(path)
        case 'rm':
            if (path := get_arg(sys.argv, 2)) is None:
                print('error: no item to delete specified')
                sys.exit(1)
            odc.rm(path)
        case 'debug-on':
            odc.debug_on(True)
        case 'debug-off':
            odc.debug_on(False)
        case other:
            print(f'ods: unknown command: {sys.argv[1]}')

if __name__ == '__main__':
    main()