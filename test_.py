import os
import sqlite3
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


class TestCD:

    def test_absolute_path(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        ods = OneDriveSynch(settings_db=test_settings_file)

        assert ods._cwd == '/root'
        ods.cd('/root/path/to/my/current/dir')
        assert ods._cwd == '/root/path/to/my/current/dir'

        if os.path.exists(test_settings_file):
                os.remove(test_settings_file)

    def test_absolute_path_double_dots(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        ods = OneDriveSynch(settings_db=test_settings_file)

        assert ods._cwd == '/root'
        ods.cd('/root/path/to/my/current/dir')
        assert ods._cwd == '/root/path/to/my/current/dir'

        ods.cd('/root/path/to/../')
        assert ods._cwd == '/root/path'

        if os.path.exists(test_settings_file):
                os.remove(test_settings_file)

    def test_double_dots(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        ods = OneDriveSynch(settings_db=test_settings_file)
        assert ods._cwd == '/root'

        ods.cd('/root/path/to/my/current/dir')
        assert ods._cwd == '/root/path/to/my/current/dir'

        # Actual test
        new_cwd = '../../'
        ods.cd(new_cwd)
        assert ods._cwd == '/root/path/to/my'

        # Check it wrote to the DB properly and can be retrieved
        db_cwd = ods._get_setting('cwd')
        assert db_cwd == '/root/path/to/my'

        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)

    def test_double_dots_either_side(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        ods = OneDriveSynch(settings_db=test_settings_file)
        assert ods._cwd == '/root'
        
        ods.cd('/root/path/to/my/current/dir')
        assert ods._cwd == '/root/path/to/my/current/dir'

        # Actualy test
        new_cwd = '../../../my/../'
        ods.cd(new_cwd)
        assert ods._cwd == '/root/path/to'
        
        # Check it wrote to the DB properly and can be retrieved
        db_cwd = ods._get_setting('cwd')
        assert db_cwd == '/root/path/to'

        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)

    def test_single_dots(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        ods = OneDriveSynch(settings_db=test_settings_file)
        assert ods._cwd == '/root'
        
        ods.cd('/root/path/to/my/current/dir')
        assert ods._cwd == '/root/path/to/my/current/dir'

        # Actual Test
        new_cwd = './'
        ods.cd(new_cwd)
        assert ods._cwd == '/root/path/to/my/current/dir'

        # Check it wrote to the DB properly and can be retrieved
        db_cwd = ods._get_setting('cwd')
        assert db_cwd == '/root/path/to/my/current/dir'

        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)

    def test_single_dots_subdirectory(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        ods = OneDriveSynch(settings_db=test_settings_file)
        assert ods._cwd == '/root'

        ods.cd('/root/path/to/my/current/dir')
        assert ods._cwd == '/root/path/to/my/current/dir'

        # Actual Test
        new_cwd = './new/path'
        ods.cd(new_cwd)
        assert ods._cwd == '/root/path/to/my/current/dir/new/path'

        db_cwd = ods._get_setting('cwd')
        assert db_cwd == '/root/path/to/my/current/dir/new/path'

        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)

    def test_single_dot_inbetween(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        ods = OneDriveSynch(settings_db=test_settings_file)
        assert ods._cwd == '/root'

        ods.cd('/root/path/to/my/current/dir')
        assert ods._cwd == '/root/path/to/my/current/dir'

        new_cwd = './new/./path'
        ods.cd(new_cwd)
        assert ods._cwd == '/root/path/to/my/current/dir/new/path'

        db_cwd = ods._get_setting('cwd')
        assert db_cwd == '/root/path/to/my/current/dir/new/path'

        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)

