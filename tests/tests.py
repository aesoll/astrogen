from os import path
import os
from textwrap import dedent
import config
from irods.session import iRODSSession
import unittest
from astrogen import astrogen

__irods_server_host__ = 'bitol.iplantcollaborative.org'
__irods_server_port__ = "1247"
__irods_server_zone__ = "iplant"

class TestAstrogen(unittest.TestCase):
    def setUp(self):
        self.test_coll_path = '/iplant/home/elyons/ACIC/midterm-Carl-Hergenrother'
        user = raw_input("Enter username: ")
        password = raw_input("Enter password: ")
        self.sess = iRODSSession(host=__irods_server_host__,
                                 port=__irods_server_port__,
                                 user=user,
                                 password=password,
                                 zone=__irods_server_zone__)
        # Create test collection
        self.test_coll = self.sess.collections.get(self.test_coll_path)

    def test_logging(self):
        try:
            if path.exists(path.join(astrogen.__pkg_root__, 'astropy.log')):
                assert True
        except OSError:
            assert False

    def tearDown(self):
        config_path = path.join(path.curdir, 'test_config.cfg')
        try:
            os.remove(config_path)
        except OSError:
            pass
        self.sess.cleanup()


class TestConfig(unittest.TestCase):
    def test_config(self):
        config_str = dedent('''\
        label:
        {
            key1 : 'value1',
            key2 : 17
        }
        ''')
        correct_key1 = 'value1'
        correct_key2 = 17

        with open('test_config.cfg', 'w') as f:
            f.write(config_str)

        with open('test_config.cfg', 'r') as f:
            cfg = config.Config(f)
            key1 = cfg.label.key1
            key2 = cfg.label.key2

        self.assertEqual(key1, correct_key1)
        self.assertEqual(key2, correct_key2)


if __name__ == '__main__':
    unittest.main()
