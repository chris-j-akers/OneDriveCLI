import sqlite3
import logging

logger = logging.getLogger(__name__)
                           
class OneDriveSynch:

# private:
    
    def __init__(self, settings_db='./settings.db') -> None:
        self._logger = logger.getChild(__class__.__name__)
        self._logger.debug('creating OneDriveSynch object')
        self._initialise_db(settings_db)
        self.cd('/root')
        pass

    def _initialise_db(self, settings_db):
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

    def _upsert_setting(self, key, value):
        self._logger.debug(f'updating value "{key}" to "{value}" in settings db')
        cursor = self._settings_db.cursor()
        cursor.execute('INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT (key) DO UPDATE SET value = ?;', (key, value, value))
        cursor.close()

    def _get_setting(self, key):
        self._logger.debug(f'getting value for "{key}" from settings db')
        cursor = self._settings_db.cursor()
        result = cursor.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchall()
        cursor.close()
        return result[0][0]

    def _wrangle_relative_path(self, path):
        self._logger.debug(f"attempting to wrangle new path from '{path}'")
        cwd = self._cwd.split('/')
        nwd = [dir for dir in path.split('/') if dir not in ['.', '']]
        for dir in nwd:
            if dir == '..':
                cwd.pop()
            else:
                cwd.append(dir)
        return cwd if len(cwd) == 1 else '/'.join(cwd)

# public:
    
    def authenticate(self):
        pass

    def cd(self, path):
        self._logger.debug(f'attempting to change directory to "{path}"')
        if path == '/':
            self._cwd = '/root'
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
        return self._cwd

    def ls(self):
        pass

    def get(remote_path, local_path):
        pass

    def put(local_path, remote_path):
        pass