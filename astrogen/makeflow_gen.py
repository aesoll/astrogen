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
import astrogen


def get_fits_filenames(fits_source_directory):
    """
    Return list of directory contents (FITS filenames) if valid directory.
    """
    if os.path.isdir(fits_source_directory):
        return os.listdir(fits_source_directory)
    raise ValueError(fits_source_directory + " is not a valid directory.")


def makeflow_gen(fits_filenames, fits_source_directory):
    """
    Write out contents of fits_filenames to properly formatted makeflow file.
    """
    makeflow_path = \
        os.path.join(astrogen.__pkg_root__, os.pardir, 'makeflows', 'output.mf')
    makeflow_file = open(makeflow_path, "w")

    with open('foo.txt', 'w') as f:
       f.write("BLAHBLAHBLAH")

    count = 0
    abs_resources_path = os.path.abspath(astrogen.__resources_dir__)
    abs_batch_path = os.path.abspath(astrogen.__batch_dir__)
    backend_config_path = \
        os.path.join(abs_resources_path, 'astrometry.cfg')
    makeflow_file.write("export PATH=/home/u12/ericlyons/bin/newnetpbm/bin:$PATH\n")  # This should only appear once at the top
    for item in fits_filenames:
        filepath = os.path.join(abs_batch_path, item)
        cmd = \
            'module load python &&'\
            '/gsfs1/xdisk/dsidi/midterm/astrometry.net\-0.50/blind/solve-field ' \
              '-g' \
              '-u app ' \
              '-L 0.3 ' \
              '-p' \
              '--cpulimit 600' \
              '--wcs none' \
              '--corr none' \
              '--scamp-ref none' \
              '--pnm none' \
              '-H 3.0 ' \
              '--backend-config {} ' \
              '--overwrite ' \
              '{}'.format(backend_config_path, filepath)
        file_name = '{}'.format(backend_config_path, filepath)
        makeflow_file.write(
            "none" + ": " + file_name + "\n")
        # TODO rm
        #     "/path/to/solve-field -u app -L 0.3 -H 3.0 --backend-config " +
        #     fits_source_directory + item + "\n"
        # )
        makeflow_file.write("\t" + cmd + "\n\n")    # + "-o output_" + str(count) + "\n\n")
        # TODO rm
        #   "/path/to/solve-field -u app -L 0.3 -H 3.0 --backend-config " +
        #   fits_source_directory + item + "-o output_" + str(count) + "\n\n"
        # )
        count += 1

    makeflow_file.close()
    return None


def main():
    """
    Call get_fits_filenames and makeflow_gen with appropriate arguments.
    """
    fits_source_directory = str(sys.argv[1])
    fits_filenames = get_fits_filenames(fits_source_directory)
    makeflow_gen(fits_filenames, fits_source_directory)
    
    return None


if __name__=="__main__":
    main()
