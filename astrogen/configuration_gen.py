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
        self.focal_length = None
        self.field_rotation = None
        self.template_filename = os.path.join(__resources_dir__,
                                              'config_template.txt')

    def process(self, fits_filename, stdout_filename):
        """

        :return:
        """
        self.get_stdout_values(stdout_filename)
        self.set_fits_headers(fits_filename)
        self.determine_focal_length()

        config_name = os.path.splitext(fits_filename) + ".cfg"
        self.set_new_cfg_headers(config_name)

    def get_stdout_values(self, stdout_filename):
        """
        Sets instance variables for extracted stdout values
        """
        with open(stdout_filename, "r") as f:
            for line in f:
                if "pixel scale" in line:
                    line_list = line.split(" ")
                    self.stdout_pixelscale = line_list[7]
                elif "(RA H:M:S, Dec D:M:S)" in line:
                    line_list = line.split(" ")
                    self.stdout_ra = line_list[7][1:-1].replace(":", " ")
                    self.stdout_dec = line_list[8][:-3].replace(":", " ")
                elif "Field rotation angle" in line:
                    line_list = line.split(" ")
                    self.field_rotation = line_list[5]

        return None

    def set_fits_headers(self, fits_filename):
        """
        Sets objctra and objctdec fits headers based on instance variables
        """
        fits_file = pyfits.open(fits_filename)
        # TODO unit test for this
        # Following lines should set headers even if they don't exist
        # If not, will add some code later
        fits_file[0].header["objctra"] = self.stdout_ra
        fits_file[0].header["objctdec"] = self.stdout_dec

        return None

        
    def determine_focal_length(self):
        """
        Set instance variable representing the value derived from the focal length equation
        focal length = (206265*.03)/platescale (pixel scale...?)
        """
        self.focal_length = (206265 * 0.03) / float(self.stdout_pixelscale)

        return None


    def set_new_cfg_headers(self, config_output_filename):
        """
        Creates a new file based on self.new_cfg_filename and replaces necessary
        parameters.

        :param config_output_filename:
        """
        template = open(self.template_filename, "r")
        new_cfg = open(config_output_filename, "w")

        for line in template:
            if "FocalLength" in line:
                new_cfg.write("FocalLength=" + str(self.focal_length) +"\n")
            elif "PA" in line and "VarPA" not in line:
                new_cfg.write("PA=" + str(self.field_rotation) +"\n")
            else:
                new_cfg.write(line)

        template.close()
        new_cfg.close()

        return None

if __name__=="__main__":
    new = ConfigFile()
    new.get_stdout_values("resources/sample_stdout.txt")
    new.set_fits_headers("output/solve_field_output/example.new")
    new.determine_focal_length()
    new.set_new_cfg_headers('output/example.cfg')
