#!/usr/bin/env python

# Pipeline for solving the astrometry of image files
# astrogen.py
#
# Authors:
#   Philipp v. Bieberstein (pbieberstein@email.arizona.edu)
#   Matt Madrid (matthewmadrid@email.arizona.edu)
#   David Sidi (dsidi@email.arizona.edu)
#   Adam Soll (adamsoll@email.arizona.edu)
"""
Preprocess image files in FITS format to be input to Astrometrica.
"""
from glob import glob
import os
import pdb
import re
import subprocess
import tempfile
import logging
import scandir
from config import Config
from datetime import datetime
import time
from astropy.io import fits
from irods.session import iRODSSession
import shutil
from configuration_gen import ConfigFile
import makeflow_gen
import zipfile

__pkg_root__ = os.path.dirname(__file__)
__resources_dir__ = os.path.abspath(os.path.join(__pkg_root__, os.pardir, 'resources'))
__output_dir__ = os.path.abspath(os.path.join(__pkg_root__, os.pardir, 'output'))
__batch_dir__ = os.path.join(__resources_dir__, 'fits_files')


class Astrogen(object):
    """
    Preprocess image files in FITS format to be input to Astrometrica.
    Retrieves astronomy data in the form of FITS files from iPlant.
    Runs astrometry on a local batch of files.
    ---NOT DONE YET---
    """
    def __init__(self):

        # get params from config file
        config_path = \
            os.path.join(__resources_dir__, 'astrogen.cfg')
        with open(config_path) as f:
            cfg = Config(f)
            self.iplant_params = dict(cfg.iplant_login_details)
            self.max_batch_size = cfg.batch_details.max_batch_size
            self.path_to_solve_field = cfg.solve_field_details.path_to_solve_field
            self.path_to_netpbm = cfg.solve_field_details.path_to_netpbm

        # uname and pword are given at command line
        self.user = raw_input("Enter iPlant username: ")
        self.password = raw_input("Enter iPlant password: ")

        # set up temporary local file directory for batches
        tempfile.tempdir = os.path.join(__pkg_root__, 'resources', 'fits_files')

        # set up logging
        logging.basicConfig(filename='astrogen.log', level=logging.INFO)
        t = time.localtime()
        logging.info(
            "Astrogen run started {day}-{mo}-{year} at {hour}:{min}:{sec}".format(
                day=t.tm_mday, mo=t.tm_mon, year=t.tm_year, hour=t.tm_hour,
                min=t.tm_min, sec=t.tm_sec))

    # PUBLIC ##################################################################

    def get_astrometry(self):
        """
        Gets the astrometry data for the FITS files in this iPlant directory.

        Note: Nothing but .fits and .arch files are allowed.
        """
        # get data objects from iPlant
        cleaned_data_objects = self._get_cleaned_data_objects()

        current_batch_size = 0
        for data_object in cleaned_data_objects:
            if current_batch_size < self.max_batch_size:
                self._add_to_local_batch(data_object)
                current_batch_size = self._get_dir_size('.')
            else:
                # call astronomy.net stuff on this batch
                self._solve_batch_astrometry()

                # clear this batch from directory
                all_batched_fits_files = glob(os.path.join(__batch_dir__, '*.fits'))
                os.remove(all_batched_fits_files)
                current_batch_size = 0

    # PRIVATE #################################################################

    def _unzipper(self, data_object):
        """
        """
        with ZipFile(data_object, 'w') as myzip:
            testZip = myzip.testzip()
            if testZip == None:  # if testZip is None then there are no bad files

                path_to_unzipper_outputs = \
                    os.path.join(__resources_dir__, 'fits_files')
                myzip.write(tempfile.NamedTemporaryFile())

            else:
                myzip.moveFileToDirectory("Unusable") #move to non working folder

            ZipFile.close()

    def _file_extension_validation(self, fits_directory):
        """
        Parses filenames in a directory to determine which files are valid solve-field candidates
        Files that do not meet criteria are removed
        """
        valid_extensions = [
            "fit", "fits", "FIT", "FITS", "fts"
        ]

        for fits_file_candidate in os.listdir(fits_directory):
            if fits_file_candidate.split(".")[1] not in valid_extensions:
                os.remove(fits_directory + "/" + fits_file_candidate)
                print("Removing invalid file \"" + fits_file_candidate + "\"...")

        return None

    def _solve_batch_astrometry(self):
        """
        Generate the makeflow script to run astrometry on a batch of local
        files.

        Assumes only FITS files in the directory.
        Assumes a working solve-field on your path.
        """
        makeflow_gen.makeflow_gen(
            os.listdir(__batch_dir__),
            self.path_to_solve_field,
            self.path_to_netpbm
        )
        self._run_makeflow('output.mf')
        self._run_parameter_extraction()
        self._move_makefile_solutions()

    def _run_parameter_extraction(self):
        """Runs parameter extraction using stored output of solve-field in the
            batch directory.
        """
        path_to_solve_field_outputs = \
            os.path.join(__resources_dir__, 'fits_files')

        # where stdout was redirected in call to makeflow
        all_stdout_files = os.path.join(path_to_solve_field_outputs, '*.out')

        for output_filename in glob(all_stdout_files):
            fits_basename = os.path.basename(output_filename)
            fits_filename = os.path.splitext(fits_basename)[0] + '.fit'
            ConfigFile().process(fits_filename, output_filename)

    def _run_makeflow(self, makeflow_script_name):
        """Runs a makeflow.

        Side-effects by generating several files for each fits file in the
        batch directory (resources/fits_files).

        :param makeflow_script_name: The absolute path of the makeflow script
            to run.
        """
        # TODO factor the sections into methods
        makeflow_project_name = 'SONORAN'
        path_to_solve_field_outputs = \
            os.path.join(__resources_dir__, 'fits_files')

        ##
        # Get the shell, stand on head so that `module load` works
        #
        echo_out = subprocess.check_output('echo $SHELL', shell=True)
        shell = os.path.basename(echo_out.strip())

        # edge case: if shell is ksh93, use 'ksh'
        if shell.startswith('ksh'):
            shell = 'ksh'

        # called for this particular shell
        module_init = '/usr/share/Modules/init/' + shell

        ##
        # build makeflow, pbs_submit_workers commands
        #
        makeflow_cmd = 'cd {outputs_dir} && ' \
              'makeflow --wrapper \'. {shell_module}\' ' \
                  '-T wq ' \
                  '-a ' \
                  '-N {project_name} ' \
              '{makeflow_script_name}'.\
            format(outputs_dir=path_to_solve_field_outputs,
                   shell_module=module_init,
                   project_name=makeflow_project_name,
                   makeflow_script_name=makeflow_script_name)

        pbs_submit_cmd = 'pbs_submit_workers ' \
                         '-d all ' \
                         '-N {project_name} ' \
                         '-p "-N {project_name} ' \
                             '-W group_list=nirav ' \
                             '-q standard ' \
                             '-l jobtype=serial ' \
                             '-l select=1:ncpus=3:mem=4gb ' \
                             '-l place=pack:shared ' \
                             '-l walltime=01:00:00 ' \
                             '-l cput=01:00:00" ' \
                         '3'.format(project_name=makeflow_project_name)

        ##
        # call commands
        #
        subprocess.check_output(pbs_submit_cmd, shell=True)
        # subprocess.check_output('sleep 5', shell=True)  # not needed
        subprocess.check_output(makeflow_cmd, shell=True)

    def _move_makefile_solutions(self):
        """Move makeflow solution files to their directory"""
        output_src = os.path.join(__resources_dir__, 'fits_files')
        other_soln_files_dst = os.path.join(__output_dir__, 'other_solution_files')
        config_dst = os.path.join(__output_dir__, 'config_files')
        modified_fits_dst = os.path.join(__output_dir__, 'modified_fits_files')

        # copy the FITS files we modified, move the cfg files we generated
        for fits_file in glob(os.path.join(output_src, '*.fit')):
            shutil.copy(fits_file, modified_fits_dst)

        for cfg_file in glob(os.path.join(output_src, '*.cfg')):
            shutil.move(cfg_file, config_dst)

        other_solution_files = \
                glob(os.path.join(output_src, '*.out')) + \
                glob(os.path.join(output_src, '*.axy')) + \
                glob(os.path.join(output_src, '*.xyls')) + \
                glob(os.path.join(output_src, '*.match')) + \
                glob(os.path.join(output_src, '*.new')) +  \
                glob(os.path.join(output_src, '*.rdls')) +  \
                glob(os.path.join(output_src, '*.solved'))

        for filename in other_solution_files:
            shutil.move(filename, other_soln_files_dst)

    def _get_cleaned_data_objects(self):
        """Get and clean data objects from an iRODS collection on iPlant."""
        iplant_params = self.iplant_params

        logging.info("Logging in to {} as {} ...".
                     format(iplant_params['host'], self.user))

        sess = iRODSSession(
            host=iplant_params['host'],
            port=iplant_params['port'],
            user=self.user,
            password=self.password,
            zone=iplant_params['zone']
        )
        coll = sess.collections.get(iplant_params['iplant_path'])
        data_objects = coll.data_objects
        cleaned_data_objects = \
            filter(lambda x: x.name.lower().endswith('.fits') or
                             x.name.lower().endswith('.arch'),
                   data_objects)
        return cleaned_data_objects

    @staticmethod
    def _extract_datetime(datetime_str):
        """Get a datetime object from the date numbers in a FITS header."""
        p = re.compile(
            r"\'(\d\d\d\d)-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)\.(\d\d\d\d\d\d)\'"
        )
        datetime_match = p.match(datetime_str)
        datetime_numbers = tuple(int(x) for x in datetime_match.groups())
        return datetime(*datetime_numbers)

    @staticmethod
    def _passes_muster(self, hdus):
        """Up or down vote on a list of hdus. Currently a no-op."""
        # TODO useful for later, if we decide to filter
        # header = hdus[0].header  # first element is primary HDU, we don't use others
        # dt = Preprocessor._extract_datetime(header['DATE-OBS'][0])
        # image_type = header['VIMTYPE'][0][1:-1].strip()
        # ao_loop_state = header['AOLOOPST'][0][1:-1].strip()
        # shutter_state = header['VSHUTTER'][0][1:-1].strip()
        return True

    @staticmethod
    def _add_to_local_batch(data_object):
        """Add a FITS file from iPlant datastore to a local batch.

        """
        # TODO decorate for IO error catching
        try:
            # write to temp. local file, to be taken in by astronomy.net
            with data_object.open('r') as irods_f:
                hdus = fits.open(irods_f)
                if Astrogen._passes_muster(hdus):
                    hdus.writeto(tempfile.NamedTemporaryFile(delete=False, dir=__batch_dir__))
        except IOError:
            logging.info('File rejected: {}.').format(data_object.name)

    @staticmethod
    def _get_dir_size(file_path):
        """Get the size in bytes of a directory."""
        return sum(
            os.path.getsize(f) for f in scandir.listdir(file_path)
                               if os.path.isfile(f)
        )

