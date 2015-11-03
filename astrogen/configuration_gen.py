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
        self.stdout_ra = None
        self.stdout_dec = None
        self.stdout_pixelscale = None


    def get_fits_headers(self, stdout_filename):
        """
        Sets instance variables for extracted header values.
        """
        with open(stdout_filename, "r") as f:
            for line in f:
                if "pixel scale" in line:
                    line_list = line.split(" ")
                    self.stdout_ra = line_list[4].split(",")[0][1:]
                    self.stdout_dec = line_list[4].split(",")[1][:-1]
                    self.stdout_pixelscale = line_list[7]

        print(self.stdout_ra)
        print(self.stdout_dec)
        print(self.stdout_pixelscale)
        


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
    new.get_fits_headers("resources/sample_stdout.txt")
    #new.set_new_cfg_headers()
