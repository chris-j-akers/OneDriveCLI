import os
import sqlite3
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from OneDriveSynch import OneDriveSynch

class TestInitialisation:

    def _create_existing_db(self, settings_db):
        db = sqlite3.connect(settings_db)
        db.autocommit = True
        cursor = db.cursor()
        cursor.execute('CREATE TABLE settings (key TEXT, value TEXT, PRIMARY KEY (key))')
        cursor.execute('INSERT INTO settings (key, value) VALUES ("cwd", "/root/my/current/path")')
        cursor.execute('INSERT INTO settings (key, value) VALUES ("root", "/root")')
        cursor.execute('INSERT INTO settings (key, value) VALUES ("drive_id", "12345678")')
        cursor.execute('INSERT INTO settings (key, value) VALUES ("is_initialised", "true")')

        cursor.execute('CREATE TABLE token (app_name TEXT, refresh_token TEXT, PRIMARY KEY (app_name))')
        cursor.execute('INSERT INTO token (app_name, refresh_token) VALUES("onedrive-synch", "a_test_token_string")')
        cursor.close()

    def test_create_from_empty_db(self):
        test_settings_file = './test_settings.db'

        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)

        ods = OneDriveSynch(settings_db=test_settings_file)

        assert os.path.exists(test_settings_file)
        assert ods._initialised == False
        assert ods._drive_id == None
        assert ods._root == None
        assert ods._cwd == None

        db = sqlite3.connect(test_settings_file)
        cursor = db.cursor()
        result = cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="token";').fetchall()
        assert result[0][0] == 'token'
        result = cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="settings";').fetchall()
        assert result[0][0] == 'settings'
        cursor.close()
        os.remove(test_settings_file)
        assert not os.path.exists(test_settings_file)

    def test_initialise_from_existing_db(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        self._create_existing_db(test_settings_file)

        assert os.path.exists(test_settings_file)
    
        ods = OneDriveSynch(settings_db=test_settings_file)

        assert ods._initialised == True
        assert ods._drive_id == '12345678'
        assert ods._root == '/root'
        assert ods._cwd == '/root/my/current/path'

        db = sqlite3.connect(test_settings_file)
        cursor = db.cursor()
        result = cursor.execute('SELECT refresh_token from token WHERE app_name = "onedrive-synch"').fetchall()
        assert result[0][0] == 'a_test_token_string'
        cursor.close()

        os.remove(test_settings_file)
        assert not os.path.exists(test_settings_file)
