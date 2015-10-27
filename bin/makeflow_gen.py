#!/usr/bin/python
#
# makeflow_gen.py
#
# Authors:
#   Philipp v. Bieberstein (pbieberstein@email.arizona.edu)
#   Matt Madrid (matthewmadrid@email.arizona.edu)
#   David Sidi (dsidi@email.arizona.edu)
#   Adam Soll (adamsoll@email.arizona.edu)
#   Matthew Shanks (mcshanks@email.arizona.edu)
"""
Generates a makeflow file for processing FITS files with the astrometry software 
solve_field.
"""


import sys
import os


def get_fits_filenames(fits_source_directory):
    """
    Return list of directory contents (FITS filenames) if valid directory.
    """
    if os.path.isdir(fits_source_directory):
        return os.listdir(fits_source_directory)
    raise ValueError(fits_source_directory + " is not a valid directory.")


def makeflow_gen(fits_filenames):
    """
    Write out contents of fits_filenames to properly formatted makeflow file.
    """
    makeflow_file = open("file", "w")

    for item in fits_filenames:
        makeflow_file.write(
            "" + "\n"
        )
        makeflow_file.write(
            "" + "\n\n"
        )

    return None


def main():
    """
    Call get_fits_filenames and makeflow_gen with appropriate arguments.
    """
    fits_filenames = get_fits_filenames(str(sys.argv[1]))
    makeflow_gen(fits_filenames)
    return None


if __name__=="__main__":
    main()