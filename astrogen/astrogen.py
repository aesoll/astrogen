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
Preprocess image files in fits format to be input to astronomy.
"""
import os
import re
import tempfile
import logging
import scandir
from config import Config
from datetime import datetime, time
from astropy.io import fits
from irods.session import iRODSSession

__pkg_root__ = os.path.dirname(__file__)


# TODO class docs
class Astrogen(object):
    """BRIEF DESCRIPTION

    MORE DETAILED DESCRIPTION

    """
    def __init__(self):
        # read config file
        with open(os.path.join(__pkg_root__, 'resources', 'astrogen.cfg')) as f:
            cfg = Config(f)
            self.iplant_params = cfg.iplant_login_details.values()
            self.max_batch_size = cfg.batch_details.max_batch_size

        # set up temporary local file directory
        tempfile.tempdir = os.path.join(__pkg_root__, 'resources', 'fits_files')

        # set up logging
        logging.basicConfig(filename='astrogen.log', level=logging.INFO)
        t = time.localtime()
        logging.info(
            "Astrogen run started {day}-{mo}-{year} at {hour}:{min}:{sec}".format(
                day=t.tm_mday, mo=t.tm_mon, year=t.tm_year, hour=t.tm_hour,
                min=t.tm_min, sec=t.tm_sec))

    # PUBLIC ##################################################################

    def get_astronomy(self):
        """Gets the astronomy for the fits files in this iPlant directory.

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
                # TODO call astronomy.net stuff on this batch
                # TODO clear this batch from directory
                current_batch_size = 0

            pass

    # PRIVATE #################################################################

    def _get_cleaned_data_objects(self):
        """Get and clean data objects from an iRODS collection on iPlant."""
        user = raw_input("Enter iPlant username: ")
        password = raw_input("Enter iPlant password: ")
        host, port, zone, iplant_path = self.iplant_params

        logging.info("Logging in to {} as {} ...".format(host, user))

        sess = iRODSSession(
            host=host,
            port=port,
            user=user,
            password=password,
            zone=zone
        )
        coll = sess.collections.get(iplant_path)
        data_objects = coll.data_objects
        cleaned_data_objects = \
            filter(lambda x: x.name.endswith('.fits') or
                             x.name.endswith('.arch'),
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
                    hdus.writeto(tempfile.NamedTemporaryFile(delete=False))
        except IOError:
            logging.info('File rejected: {}.').format(data_object.name)

    @staticmethod
    def _get_dir_size(file_path):
        """Get the size in bytes of a directory."""
        return sum(
            os.path.getsize(f) for f in scandir.listdir(file_path)
                               if os.path.isfile(f)
        )
