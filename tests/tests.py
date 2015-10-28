from os import path
import os
from textwrap import dedent
import config
from irods.session import iRODSSession
import unittest
from astrogen import astrogen
from astrogen.astrogen import Astrogen

__irods_server_host__ = 'bitol.iplantcollaborative.org'
__irods_server_port__ = "1247"
__irods_server_zone__ = "iplant"

class TestAstrogen(unittest.TestCase):
    def setUp(self):
        self.ag = Astrogen()
        self.ag.iplant_params = {
            'host': 'bitol.iplantcollaborative.org',
            'port': 1247,
            'zone': 'iplant',
            'iplant_path': '/iplant/home/david_sidi/astrometry/test_fits'
        }

    def test_get_cleaned_data_objects(self):
        cleaned_objs = self.ag._get_cleaned_data_objects()
        names = [obj.name for obj in cleaned_objs]
        correct_names = [
            'V47_20141104053006072910.fits',
            'V47_20141104053006356387.fits',
            'V47_20141104053006639865.fits',
            'V47_20141104053006923346.fits',
            'V47_20141104053007206822.fits',
            'V47_20141104053007490300.fits',
            'V47_20141104053007773776.fits',
            'V47_20141104053008057255.fits',
            'V47_20141104053008340735.fits'
        ]
        self.assertListEqual(names, correct_names)

    def test_batching(self):
        assert True

    def test_logging(self):
        try:
            if path.exists(path.join(astrogen.__pkg_root__, 'astropy.log')):
                assert True
        except OSError:
            assert False

    def test_iplant_fetch(self):
        self.test_coll_path = '/iplant/home/elyons/ACIC/midterm-Carl-Hergenrother'

        # get user and pword from user entry when astrogen was constructed
        user = self.ag.user
        password = self.ag.password

        self.sess = iRODSSession(host=__irods_server_host__,
                                 port=__irods_server_port__,
                                 user=user,
                                 password=password,
                                 zone=__irods_server_zone__)
        self.test_coll = self.sess.collections.get(self.test_coll_path)
        self.sess.cleanup()

    def tearDown(self):
        config_path = path.join(path.curdir, 'test_config.cfg')
        try:
            os.remove(config_path)
        except OSError:
            pass


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
