#!/usr/bin/python
#
# test-astrometrica-gen.py
#
# Authors:
#   Philipp v. Bieberstein (pbieberstein@email.arizona.edu)
#   Matt Madrid (matthewmadrid@email.arizona.edu)
#   David Sidi (dsidi@email.arizona.edu)
#   Adam Soll (adamsoll@email.arizona.edu)
"""

"""


import unittest
from ..bin.astrometriconf import *


class TestGetFitsFilenames(unittest.TestCase):
    """
    Test to confirm specified source directory is a valid directory
    """
    def setUp(self):
        self.source_directory_1 = "../"
        self.source_directory_2 = "../README.md"


    def test_get_fits_filenames(self):
        self.assertRaises(ValueError, get_fits_filenames(self.source_directory_2))


class TestBuildDataframe(unittest.TestCase):
    """
    """
    def setUp(self):
    	pass


    def test_build_dataframe(self):
    	pass


class TestPassesMaster(unittest.TestCase):
    """
    """
    def setUp(self):
    	pass


    def test_passes_master(self):
    	pass


class TestSolveField(unittest.TestCase):
    """
    """
    def setUp(self):
    	pass


    def test_solve_field(self):
    	pass


class GenerateAstroConfig(unittest.TestCase):
    """
    """
    def setUp(self):
    	pass


    def test_generate_astro_config(self):
    	pass


if __name__=="__main__":
	unittest.main()