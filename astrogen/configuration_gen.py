#!/usr/bin/python
#
# configuration_gen.py
#
# Authors:
#   Philipp v. Bieberstein (pbieberstein@email.arizona.edu)
#   Matt Madrid (matthewmadrid@email.arizona.edu)
#   David Sidi (dsidi@email.arizona.edu)
#   Adam Soll (adamsoll@email.arizona.edu)
#   Matthew Shanks (mcshanks@email.arizona.edu)
"""
Generates a new configuration file for use with Astrometrica
"""
from astropy.io import fits
import os
import astrogen
import pyfits
import sys

__pkg_root__ = os.path.dirname(__file__)
__resources_dir__ = os.path.join(__pkg_root__, os.pardir, 'resources')
__batch_dir__ = os.path.join(__resources_dir__, 'fits_files')
__output_dir__ = os.path.join(__pkg_root__, os.pardir, 'output')


class ConfigFile(object):
    def __init__(self):
        """
        Initialize instance variables representing the fits filename,
        the template for the configuration file, the new configuration file
        output name, and the two parameters to replace. 
        """
        self.fits_filename = os.path.join(astrogen.__output_dir__, "solve_field_output", "example.new")
        self.fits_file = pyfits.open(self.fits_filename)
        self.fits_file.info()
        self.template_filename = os.path.join(astrogen.__resources_dir__, "config_template.txt")
        #self.new_cfg_filename = str(self.fits_file[0].header[""]).replace(":", "")
        self.new_cfg_filename = "example_output.cfg"
        self.cfg_param_1 = "FocalLength"
        self.cfg_param_2 = "PA"


    def get_fits_headers(self):
        """
        Sets instance variables for extracted header values.
        """
        self.extracted_objctra = self.fits_file[0].header["objctra"]
        self.extracted_objctdec = self.fits_file[0].header["objctdec"]
        print()
        print("objectra: " + self.extracted_objctra)
        print("objectdec: " + self.extracted_objctdec)


    def set_new_cfg_headers(self):
        """
        Creates a new file based on self.new_cfg_filename and replaces necessary
        parameters.
        """
        new_cfg_path = os.path.join(astrogen.__output_dir__, "configuration_gen_output", self.new_cfg_filename)
        template = open(self.template_filename, "r")
        new_cfg = open(new_cfg_path, "w")

        for line in template:
            if self.cfg_param_1 in line:
                new_cfg.write(self.cfg_param_1 + "=" + self.extracted_objctra +"\n")
            elif self.cfg_param_2 in line:
                new_cfg.write(self.cfg_param_2 + "=" + self.extracted_objctdec +"\n")
            else:
                new_cfg.write(line)

        template.close()
        new_cfg.close()

if __name__=="__main__":
    new = ConfigFile()
    new.get_fits_headers()
    new.set_new_cfg_headers()
