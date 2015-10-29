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

"""
from astropy.io import fits


__pkg_root__ = os.path.dirname(__file__)
__resources_dir__ = os.path.join(__pkg_root__, os.pardir, 'resources')
__batch_dir__ = os.path.join(__resources_dir__, 'fits_files')


class ConfigFile(object):
    """
    """
    def __init__(self, fits_filename, template_filename):
        """
        """
        self.fits_file = fits.open(fits_filename)
        self.template_filename = ""
        self.new_cfg_filename = str(self.fits_file.header[""]).replace(":", "")
        self.cfg_param_1 = "FocalLength"
        self.cfg_param_2 = "PA"


    def set_fits_headers(self):
        """
        """
        self.extracted_header_1 = self.fits_file.header[""]
        self.extracted_header_2 = self.fits_file.header[""]


    def set_new_cfg_headers(self):
        """
        """
        template = open(template_filename, "r")
        new_cfg = open(self.new_cfg_filename, "w")

        for line in template:
            if self.cfg_param_1 in line:
                new_cfg.write(self.cfg_param_1 + "=" + self.extracted_header_1)
            elif self.cfg_param_2 in line:
                new_cfg.write(self.cfg_param_2 + "=" + self.extracted_header_2)
            else
                new_cfg.write(line)

        template.close()
        new_cfg.close()
