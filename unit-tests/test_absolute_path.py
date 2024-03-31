import os
import sqlite3
import logging
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from OneDriveCLI import OneDriveCLI

logging.getLogger().setLevel(logging.DEBUG)

class TestAbsolutePath:

    def test_absolute_path(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        ods = OneDriveCLI(settings_db=test_settings_file)

        cwd = '/'
        nwd = ods._get_absolute_path(cwd, '/root/path/to/my/current/dir')
        assert nwd == '/root/path/to/my/current/dir'

        if os.path.exists(test_settings_file):
                os.remove(test_settings_file)

    def test_absolute_path_double_dots(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        ods = OneDriveCLI(settings_db=test_settings_file)
        
        cwd = '/path/to/my/current/dir'    
        nwd = ods._get_absolute_path(cwd, '/path/to/../')
        assert nwd == '/path'

        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)

    def test_double_dots(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        ods = OneDriveCLI(settings_db=test_settings_file)
        
        cwd = '/path/to/my/current/dir'
        nwd = ods._get_absolute_path(cwd, '../../')
        assert nwd == '/path/to/my'

        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)

    def test_double_dots_either_side(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        ods = OneDriveCLI(settings_db=test_settings_file)
        
        cwd = '/path/to/my/current/dir'
        nwd = ods._get_absolute_path(cwd, '../../../my/../' )
        assert nwd == '/path/to'

        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)

    def test_single_dots(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        ods = OneDriveCLI(settings_db=test_settings_file)
        
        cwd = '/path/to/my/current/dir'
        nwd = ods._get_absolute_path(cwd, './')
        assert nwd == '/path/to/my/current/dir'

        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)

    def test_single_dots_subdirectory(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        ods = OneDriveCLI(settings_db=test_settings_file)

        cwd = ('/path/to/my/current/dir')
        # Actual Test
        nwd = ods._get_absolute_path(cwd, './new/path')
        assert nwd == '/path/to/my/current/dir/new/path'

        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)

    def test_single_dot_inbetween(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        ods = OneDriveCLI(settings_db=test_settings_file)

        cwd = '/path/to/my/current/dir'
        nwd = ods._get_absolute_path(cwd, './new/./path')
        assert nwd == '/path/to/my/current/dir/new/path'

        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)

    def test_root(self):
        test_settings_file = './test_settings.db'
        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)
        ods = OneDriveCLI(settings_db=test_settings_file)

        cwd = '/path/to/my/current/dir'
        nwd = ods._get_absolute_path(cwd, '/')
        assert nwd == '/'

        if os.path.exists(test_settings_file):
            os.remove(test_settings_file)