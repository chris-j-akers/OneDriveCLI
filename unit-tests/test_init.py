import os
import sqlite3
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from OneDriveSynch import OneDriveSynch

class TestInitialisation:

    def test_initialise_from_empty_db(self):
        test_settings_file = './test_settings.db'

        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)

        ods = OneDriveSynch(settings_db=test_settings_file)

        assert os.path.exists(test_settings_file)
        assert ods._cwd == '/root'

        cursor = ods._settings_db.cursor()
        result = cursor.execute('SELECT value FROM settings WHERE key = "cwd"').fetchall()
        assert result[0][0] == '/root'
        cursor.close()

        os.remove(test_settings_file)
        assert not os.path.exists(test_settings_file)

    def _create_existing_db(self, settings_db):
        db = sqlite3.connect(settings_db)
        db.autocommit = True
        cursor = db.cursor()
        cursor.execute('CREATE TABLE settings (key TEXT, value TEXT, PRIMARY KEY (key))')
        cursor.execute('INSERT INTO settings (key, value) VALUES ("cwd", "/root/my/current/path")')
        cursor.close()

    def test_initialise_from_existing_db(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        self._create_existing_db(test_settings_file)

        assert os.path.exists(test_settings_file)
    
        db = sqlite3.connect(test_settings_file)

        cursor = db.cursor()
        result = cursor.execute('SELECT value FROM settings WHERE key = "cwd"').fetchall()
        assert result[0][0] == '/root/my/current/path'
        cursor.close()

        os.remove(test_settings_file)
        assert not os.path.exists(test_settings_file)
