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
Scalably solve astrometry for image files in FITS format to produce
configuration files for Astrometrica.
"""
import getpass
import os
import re
import subprocess
import tempfile
import logging
import shutil
import time
from irods.exception import CAT_UNKNOWN_COLLECTION, UserInputException
import makeflow_gen
import pdb
from glob import glob
from datetime import datetime
from zipfile import ZipFile
from config import Config
from astropy.io import fits
from irods.session import iRODSSession
from configuration_gen import ConfigFile

__pkg_root__ = os.path.dirname(__file__)
__resources_dir__ = os.path.join(__pkg_root__, os.pardir, 'resources')
__output_dir__ = os.path.join(__pkg_root__, os.pardir, 'output')
__batch_dir__ = os.path.join(__resources_dir__, 'fits_files')


class Astrogen(object):
    """
    Preprocesses image files in FITS format, filtering bad files.
    Retrieves astronomy data in the form of FITS files from iPlant.
    Solves astrometry of a local batch of files, generating (among other things)
    a working configuration file for Astrometrica.
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
        self.password = getpass.getpass("Enter iPlant password: ")

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
        cleaned_data_objects = self._get_data_objects()

        current_batch_size = 0
        for data_object in cleaned_data_objects:
            if current_batch_size < self.max_batch_size:
                self._add_to_local_batch(data_object)
                #current_batch_size = os.path.getsize(__batch_dir__) / 1024. ** 2
                current_batch_size = \
                   sum(
                         [os.path.getsize(f) for f in os.listdir(__batch_dir__) 
                            if os.path.isfile(f)]
                   ) / 1024. ** 2
            else:
                # call astronomy.net stuff on this batch
                self._solve_batch_astrometry()

                # clear this batch from directory
                all_batched_fits_files = glob(os.path.join(__batch_dir__, '*'))
                os.remove(all_batched_fits_files)
                current_batch_size = 0

    # PRIVATE #################################################################

    def _unzipper(self, data_object):
        """
        Checks if file can be unzip and if it can sends it to resources/fit_files
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
        fits_filenames = os.listdir(__batch_dir__)
        makeflow_gen.makeflow_gen(
            fits_filenames,
            self.path_to_solve_field,
            self.path_to_netpbm
        )
        makeflow_path = os.path.join(__output_dir__, 'makeflows', 'output.mf')
        self._run_makeflow(makeflow_path)
        self._run_parameter_extraction()
        self._move_makeflow_solutions()

    @staticmethod
    def _run_parameter_extraction():
        """Runs parameter extraction using stored output of solve-field in the
            batch directory.
        """
        path_to_solve_field_outputs = \
            os.path.join(__resources_dir__, 'fits_files')

        # where stdout was redirected in call to makeflow
        all_stdout_files = os.path.join(path_to_solve_field_outputs, '*.out')

        for output_filename in glob(all_stdout_files):
            is_not_empty = os.path.getsize(output_filename)
            if is_not_empty:
                dir_name = os.path.dirname(output_filename)
                fits_basename = os.path.basename(output_filename)
                fits_filename = os.path.splitext(fits_basename)[0] + '.fit'
                fits_path = os.path.join(dir_name, fits_filename)
                ConfigFile().process(fits_path, output_filename)

    @staticmethod
    def _run_makeflow(makeflow_script_name):
        """Runs a makeflow.

        Side-effects by generating several files for each fits file in the
        batch directory (resources/fits_files).

        WARNING: Clears previous runs from the makeflows directory.

        :param makeflow_script_name: The absolute path of the makeflow script
            to run.
        """
        # self._clear_generated_files()

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
        #TODO modify temp files locations
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
        print ('Now calling makeflow and pbs_submit_workers (you may want to '
              'watch the resources/fits_files directory for .out files in a '
              'couple of minutes) ...')
        pbs_output_dst = os.path.join(__resources_dir__, 'pbs_output')  # TODO add date to fn
        makeflow_output_dst = os.path.join(__resources_dir__, 'makeflow_output')  # TODO add date
        

        with open(pbs_output_dst, 'w') as f1, open(makeflow_output_dst, 'w') as f2:
           subprocess.Popen(pbs_submit_cmd, shell=True, stdout=f1)
           subprocess.Popen(makeflow_cmd, shell=True, stdout=f2)

        print ('... batch complete.')
        t = time.localtime()
        logging.info('finished a batch on {day}-{mo}-{year} at {hour}:{min}:{sec}'.format(
                day=t.tm_mday, mo=t.tm_mon, year=t.tm_year, hour=t.tm_hour,
                min=t.tm_min, sec=t.tm_sec))

    def _move_makeflow_solutions(self):
        """Move makeflow solution files to their directory
        Issuing shell commands like `imv` is not done because it is not
         portable (even though it would be simpler).
        """
        def mk_irods_path(leaf_dir):
            return os.path.join(
                self.iplant_params['iplant_write_path'],
                leaf_dir
            )

        iplant_params = self.iplant_params
        logging.info("Writing data to {} as {} ...".
                     format(iplant_params['host'], self.user))

        sess = self._get_irods_session()
        output_src = os.path.join(__resources_dir__, 'fits_files')

        fits_file_paths = glob(os.path.join(output_src, '*.fit'))
        cfg_file_paths = glob(os.path.join(output_src, '*.cfg'))
        other_soln_file_paths = \
            glob(os.path.join(output_src, '*.out')) + \
            glob(os.path.join(output_src, '*.axy')) + \
            glob(os.path.join(output_src, '*.xyls')) + \
            glob(os.path.join(output_src, '*.match')) + \
            glob(os.path.join(output_src, '*.new')) + \
            glob(os.path.join(output_src, '*.rdls')) + \
            glob(os.path.join(output_src, '*.solved'))

        # list of lists created by combining globs
        lists_of_file_paths = [fits_file_paths, cfg_file_paths, other_soln_file_paths]

        irods_fits_output_dst = mk_irods_path('modified_fits')
        irods_cfg_output_dst = mk_irods_path('astrometrica_config_files')
        irods_other_soln_output_dst = mk_irods_path('other_solution_files')

        output_dsts = [irods_fits_output_dst, irods_cfg_output_dst,
                       irods_other_soln_output_dst]

        for soln_file_paths, output_dst in zip(lists_of_file_paths, output_dsts):
            self._move_to_irods_store(sess, output_src, soln_file_paths, output_dst)

    def _get_irods_session(self):
        iplant_params = self.iplant_params
        return iRODSSession(
            host=iplant_params['host'],
            port=iplant_params['port'],
            user=self.user,
            password=self.password,
            zone=iplant_params['zone']
        )

    def _move_to_irods_store(self, sess, output_src, files_glob, output_irods_dst):
        """Move files to an irods store.

        Note: overwrites files that are identically named.

        :param output_irods_dst:
        :param files_glob:
        :param output_src:
        :param sess:
        :return:
        """
        try:
            sess.collections.create(output_irods_dst)
        except:  # TODO get exception name
            pass
            
        for filename in files_glob:
            basename = os.path.basename(filename)
            iplant_filepath = os.path.join(output_irods_dst, basename)

            # create irods file to store the local file
            try:
                obj = sess.data_objects.create(iplant_filepath)
            except UserInputException as e: 
               logging.info("File {} not moved. Exception details: {}".
                     format(filename, e))
               continue
            finally:
               os.remove(filename)

            # copy the local file
            with obj.open('w+') as f, open(filename, 'r') as g:
                f.write(g.read())

            # TODO rm local file

    def _get_data_objects(self):
        """Get and clean data objects from an iRODS collection on iPlant."""
        iplant_params = self.iplant_params

        logging.info("Reading data from {} as {} ...".
                     format(iplant_params['host'], self.user))

        sess = self._get_irods_session()
        coll = sess.collections.get(iplant_params['iplant_filepath'])
        data_objects = coll.data_objects
        # cleaned_data_objects = \
        #     filter(lambda x: x.name.lower().endswith('.fits') or
        #                      x.name.lower().endswith('.arch'),
        #            data_objects)
        return data_objects

    @staticmethod
    def _clear_generated_files():
        """Clears the files generated by the pipeline."""
        erase_fits = raw_input("Erase all non FITS files from {} (y/n)?".format(__batch_dir__))

        if erase_fits.lower() == 'y':
            print "Erasing..."
            try:
                for filename in os.listdir(__batch_dir__):
                    if not filename.lower().endswith('*.fit'):
                        os.remove(filename)
            except:
                logging.error("Could not erase files from {}".format(__batch_dir__))
        else:
            print "Not erasing..."


        makeflows_dir = os.path.join(__output_dir__, 'makeflows')
        erase_makeflows = raw_input("Erase all files from {} (y/n)?".format(makeflows_dir))
        if erase_makeflows.lower() == 'y':
            print "Erasing..."
            try:
                map(os.remove, glob(os.path.join(makeflows_dir, '*')))
            except:
                logging.error("Could not erase files from {}".format(makeflows_dir))
        else:
            print "Not Erasing..."

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
    def _passes_muster(hdus):
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
            name = data_object.name
            # write to temp. local file
            filepath = os.path.join(__batch_dir__, name)
            with open(filepath, 'w') as f:
                with data_object.open('r') as irods_f:
                   f.write(irods_f.read())
        except IOError:
            logging.info('File rejected: {}.'.format(data_object.name))

