import os
import sqlite3
import logging
from src.OneDriveCLI.OneDriveCLI import OneDriveCLI

logging.getLogger().setLevel(logging.DEBUG)

class TestDB:
        
    def test_insert_new_setting(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        ods = OneDriveCLI(settings_db=test_settings_file)

        key = 'my_setting'
        val = 'value'

        db = sqlite3.connect(test_settings_file)
        cursor = db.cursor()
        result = cursor.execute('SELECT value from settings WHERE key == ?', (key,)).fetchall()
        assert len(result) == 0
        cursor.close()

        ods._upsert_setting(key, val)

        cursor = db.cursor()
        result = cursor.execute('SELECT value from settings WHERE key == ?', (key,)).fetchall()
        assert len(result) == 1
        assert result[0][0] == val
        cursor.close()

        os.remove(test_settings_file)
        assert not os.path.exists(test_settings_file)

    def test_update_setting(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        ods = OneDriveCLI(settings_db=test_settings_file)

        key = 'my_setting'
        val = 'value'

        db = sqlite3.connect(test_settings_file)
        cursor = db.cursor()
        result = cursor.execute('SELECT value from settings WHERE key == ?', (key,)).fetchall()
        assert len(result) == 0
        cursor.close()

        ods._upsert_setting(key, val)

        cursor = db.cursor()
        result = cursor.execute('SELECT value from settings WHERE key == ?', (key,)).fetchall()
        assert len(result) == 1
        assert result[0][0] == val
        cursor.close()

        val = 'new_value'
        ods._upsert_setting(key, val)

        cursor = db.cursor()
        result = cursor.execute('SELECT value from settings WHERE key == ?', (key,)).fetchall()
        assert len(result) == 1
        assert result[0][0] == val
        cursor.close()

        os.remove(test_settings_file)
        assert not os.path.exists(test_settings_file)

    def test_get_setting(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        ods = OneDriveCLI(settings_db=test_settings_file)

        key = 'my_setting'
        val = 'value'

        db = sqlite3.connect(test_settings_file)
        cursor = db.cursor()
        result = cursor.execute('SELECT value from settings WHERE key == ?', (key,)).fetchall()
        assert len(result) == 0
        cursor.close()

        ods._upsert_setting(key, val)
        setting = ods._get_setting(key)
        assert setting == val

        os.remove(test_settings_file)
        assert not os.path.exists(test_settings_file)
