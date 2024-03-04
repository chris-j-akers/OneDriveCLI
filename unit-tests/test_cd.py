import os
import sqlite3
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from OneDriveSynch import OneDriveSynch

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

    def test_root(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        ods = OneDriveSynch(settings_db=test_settings_file)
        assert ods._cwd == '/root'

        ods.cd('/root/path/to/my/current/dir')
        assert ods._cwd == '/root/path/to/my/current/dir'

        new_cwd = '/'
        ods.cd(new_cwd)
        assert ods._cwd == '/root'

        db_cwd = ods._get_setting('cwd')
        assert db_cwd == '/root'

        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)