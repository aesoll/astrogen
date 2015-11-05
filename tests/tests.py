from glob import glob
import unittest
import shutil
import astrogen
import os
import config
import makeflow_gen
import pdb
from os import path
from textwrap import dedent
from irods.session import iRODSSession

__irods_server_host__ = 'bitol.iplantcollaborative.org'
__irods_server_port__ = "1247"
__irods_server_zone__ = "iplant"
__test_dir__ = os.path.join(astrogen.__pkg_root__, os.pardir, 'tests')

# TODO
# * test for run_parameter_extraction to be sure all and only desired files
#   are used
class TestAstrogen(unittest.TestCase):
    def setUp(self):
        astrogen.__batch_dir__ = os.path.join(__test_dir__, 'fits_files')
        ag = astrogen.Astrogen()

        # set parameters normally gotten from astrogen.cfg
        ag.iplant_params = {
            'host': 'bitol.iplantcollaborative.org',
            'port': 1247,
            'zone': 'iplant',
            'iplant_path': '/iplant/home/david_sidi/astrometry/test_fits'
        }
        ag.path_to_netpbm = '/home/u12/ericlyons/bin/newnetpbm/bin'
        ag.path_to_solve_field = '/gsfs1/xdisk/dsidi/midterm/astrometry.net\-0.50/blind/solve-field'
        self.ag = ag

    def test_get_cleaned_data_objects(self):
        cleaned_objs = self.ag._get_cleaned_data_objects()
        names = [obj.name for obj in cleaned_objs]
        pass
        # TODO update filenames here, and uncomment assertion
        # correct_names = [
        # Briol_1197Rhodesia_20140630_044345_TA_FITS.fit
        # Briol_1197Rhodesia_20140630_044345_flatfield_TA_FITS.fit
        # Briol_1197Rhodesia_20140630_053258_TA_FITS.fit
        # Briol_1197Rhodesia_20140630_055229_TA_FITS.fit
        # Briol_1197Rhodesia_20140630_055229_flatfield_TA_FITS.FIT
        # Briol_1197Rhodesia_20140704_045604_TA_FITS.fit
        # Briol_1197Rhodesia_20140704_052116_TA_FITS.fit
        # Briol_1197Rhodesia_20140704_053610_TA_FITS.fit
        # Briol_1197Rhodesia_20140706_041323_TA_FITS.fit
        # Briol_1197Rhodesia_20140706_042914_TA_FITS.fit
        # Briol_1197Rhodesia_20140706_044914_TA_FITS.fit
        # Briol_1241Dysona_20150214_010819_TA_FITS.fit
        # Briol_1241Dysona_20150214_020103_TA_FITS.fit
        # Briol_1241Dysona_20150214_022401_TA_FITS.fit
        # ]
        # self.assertListEqual(names, correct_names)

    def test_solve_batch_astronomy(self):
        # TODO this side-effects a lot, test for a run with a single FITS
        # file in a test fits_files dir
        self.ag._solve_batch_astrometry()

    def test_batching(self):
        full_dataset_ag = astrogen.Astrogen()
        cleaned_objects = full_dataset_ag._get_cleaned_data_objects()

        current_batch_size = 0
        for data_object in cleaned_objects:
            if current_batch_size < self.max_batch_size:
                self._add_to_local_batch(data_object)
                current_batch_size = self._get_dir_size('.')
            else:
                # call astronomy.net stuff on this batch
                self._solve_batch_astrometry()

                # clear this batch from directory
                all_batched_fits_files = glob(os.path.join(astrogen.__batch_dir__, '*.fits'))
                os.remove(all_batched_fits_files)
                current_batch_size = 0

                break  # in test only, stop after first batch

        dir_size = os.path.getsize(astrogen.__batch_dir__) / 1024.
        self.assertEqual(dir_size, 100)

    def test_logging(self):
        try:
            if path.exists(path.join(astrogen.__pkg_root__, os.pardir,
                                     'resources', 'astrogen.log')):
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

    def test_run_makeflow(self):
        actual_stdout = self.ag._run_makeflow(os.path.join(astrogen.__output_dir__, 'makeflows', 'output.mf'))
        actual_log_odds = actual_stdout[-12]
        actual_RA_DEC = actual_stdout[-11]
        actual_stdout_tail = actual_stdout[-9:]

        correct_log_odds = 'log-odds ratio 113.642 (2.25997e+49), 19 match, 0 conflict, 67 distractors, 32 index.'
        correct_RA_DEC = 'RA,Dec = (358.242,64.0045), pixel scale 2.05136 arcsec/pix.'
        correct_stdout_tail = dedent("""\
            Field 1: solved with index index-4207-03.fits.
            Field 1 solved: writing to file ./Briol_2011UW158_20150727_061740_TA_FITS.solved to indicate this.
            Field: Briol_2011UW158_20150727_061740_TA_FITS.fit
            Field center: (RA,Dec) = (358.2, 64) deg.
            Field center: (RA H:M:S, Dec D:M:S) = (23:52:58.233, +64:00:14.433).
            Field size: 47.5702 x 35.535 arcminutes
            Field rotation angle: up is -152.913 degrees E of N
            Creating new FITS file "./Briol_2011UW158_20150727_061740_TA_FITS.new"...

        """)
        self.assertEqual(actual_log_odds, correct_log_odds)
        self.assertEqual(actual_RA_DEC, correct_RA_DEC)
        self.assertEqual(actual_stdout_tail, correct_stdout_tail)

    def test_clear_generated_files(self):
        makeflows_dir = os.path.join(astrogen.__output_dir__, 'makeflows')
        fits_dir = os.path.join(astrogen.__resources_dir__, 'fits_files')

        astrogen.Astrogen._clear_generated_files()

        self.assertListEqual(os.listdir(os.listdir(makeflows_dir)), [])

        num_fits = len(glob(fits_dir, '*.fit'))
        self.assertEqual(num_fits, os.listdir(fits_dir))

    def run_run_makeflow(self):
        # new ag, since the test one for this class uses tests/fits_files, but
        # we want resources/fits_files
        new_ag = astrogen.Astrogen()
        new_ag._run_makeflow(os.path.join(astrogen.__output_dir__, 'makeflows', 'output.mf'))

    def tearDown(self):
        config_path = path.join(path.curdir, 'test_config.cfg')
        try:
            os.remove(config_path)
            os.remove(os.path.join(astrogen.__resources_dir__, 'fits_files',
                                   'Briol_2011UW158_20150727_061740_TA_FITS.fit'))
            all_files_in_makeflows_dir = glob(os.path.join(astrogen.__output_dir__,
                                                           'makeflows', '*'))
            os.remove(all_files_in_makeflows_dir)
        except OSError:
            pass


class TestMakeflowGen(unittest.TestCase):

    def run_batch_makeflow_gen(self):
        """Makes a makeflow script for a batch of test fits files"""
        # fits_filenames = ['Briol_1197Rhodesia_20140630_044345_flatfield_TA_FITS.fit']
        fits_filenames = os.listdir(os.path.join(__test_dir__, 'fits_files'))

        # temporarily copy the test files to resources/fits_files
        for filename in fits_filenames:
            abs_file_path = os.path.join(__test_dir__, 'fits_files', filename)
            shutil.copy(abs_file_path, os.path.join(astrogen.__resources_dir__, 'fits_files'))

        # TODO get these from config file in tests dir
        path_to_netpbm = '/home/u12/ericlyons/bin/newnetpbm/bin'
        path_to_solve_field = '/gsfs1/xdisk/dsidi/midterm/astrometry.net-0.50/blind/solve-field'

        makeflow_gen.makeflow_gen(fits_filenames, path_to_solve_field, path_to_netpbm)

    def test_makeflow_gen(self):
        fits_filenames = ['Briol_1197Rhodesia_20140630_044345_flatfield_TA_FITS.fit']

        # temporarily copy the test file to resources/fits_files
        abs_file_path = os.path.join(__test_dir__, 'fits_files', fits_filenames[0])
        shutil.copy(abs_file_path, os.path.join(astrogen.__resources_dir__, 'fits_files'))

        # TODO get these from config file in tests dir
        path_to_netpbm = '/home/u12/ericlyons/bin/newnetpbm/bin'
        path_to_solve_field = '/gsfs1/xdisk/dsidi/midterm/astrometry.net-0.50/blind/solve-field'

        makeflow_gen.makeflow_gen(fits_filenames, path_to_solve_field, path_to_netpbm)

        ##
        # get actual output of makeflow_gen
        #
        makeflow_path = os.path.join(astrogen.__output_dir__, 'makeflows', 'output.mf')
        with open(makeflow_path) as f:
            actual_output = f.read()

        ##
        # get correct output
        #
        correct_output_filename = 'Briol_1197Rhodesia_20140630_044345_flatfield_TA_FITS.out'
        correct_fits_file_abs_path = \
            os.path.join(astrogen.__resources_dir__, 'fits_files',
                         'Briol_1197Rhodesia_20140630_044345_flatfield_TA_FITS.fit')
        correct_cfg_path = os.path.join(astrogen.__resources_dir__, 'astrometry.cfg')

        solve_field_fixed_params =\
            '-g ' \
            '-u app ' \
            '-L 0.3 ' \
            '-p ' \
            '--cpulimit 600 ' \
            '--wcs none ' \
            '--corr none ' \
            '--scamp-ref none ' \
            '--pnm none ' \
            '-H 3.0'

        correct_output = dedent("""\
            export PATH={netpbm_loc}:$PATH
            {output_filename} : {fits_file_loc} {solve_field_path}
            \tmodule load python && {solve_field_path} {solve_field_params} --backend-config {config_loc} --overwrite {fits_file_loc} > {output_filename}

            """.format(netpbm_loc=path_to_netpbm,
                       solve_field_loc=path_to_solve_field,
                       output_filename=correct_output_filename,
                       config_loc=correct_cfg_path,
                       fits_file_loc=correct_fits_file_abs_path,
                       solve_field_path=path_to_solve_field,
                       solve_field_params=solve_field_fixed_params)
        )

        self.assertEqual(actual_output, correct_output)

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
