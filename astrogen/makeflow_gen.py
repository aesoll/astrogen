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


def makeflow_gen(fits_filenames, path_to_solve_field, path_to_netpbm):
    """Write out contents of fits_filenames to properly formatted makeflow file.

    :param path_to_netpbm: The absolute path to netpbm.
    :param path_to_solve_field: The absolute path to solve field.
    """
    makeflow_path = \
        os.path.join(astrogen.__output_dir__, 'makeflows', 'output.mf')
    makeflow_file = open(makeflow_path, "w")

    abs_resources_path = os.path.abspath(astrogen.__resources_dir__)
    backend_config_path = os.path.join(abs_resources_path, 'astrometry.cfg')
    input_path = os.path.join(abs_resources_path, 'fits_files')

    # This should only appear once at the top
    makeflow_file.write("export PATH={}:{}:$PATH\n".
                        format(path_to_solve_field, path_to_netpbm))

    for filename in fits_filenames:
        output_filename = os.path.splitext(filename) + '.out'
        makeflow_file.write(
            '{output_filename}: {path_to_input_fits} solve-field\n'
            '\tmodule load python && '
            'solve-field {path_to_input_fits} '
                '-g '
                '-u app '
                '-L 0.3 '
                '-p '
                '--cpulimit 600 '
                '--wcs none '
                '--corr none '
                '--scamp-ref none '
                '--pnm none '
                '-H 3.0 '
                '--backend-config {path_to_config} '
                '--overwrite {path_to_input_fits} '
            '> {output_filename}\n\n'.
            format(
                output_filename=output_filename,
                path_to_input_fits=input_path,
                path_to_config=backend_config_path
            )
        )
    makeflow_file.close()
    return None


def main():
    """
    DEPRECATED. This script is called from astrogen. The parameters below
    are specific to our environment, and will break on others.

    Call get_fits_filenames and makeflow_gen with appropriate arguments.
    """
    path_to_netpbm = '/home/u12/ericlyons/bin/newnetpbm/bin'
    path_to_solve_field = '/gsfs1/xdisk/dsidi/midterm/astrometry.net\-0.50/blind/solve-field'
    fits_source_directory = str(sys.argv[1])
    fits_filenames = get_fits_filenames(fits_source_directory)
    makeflow_gen(fits_filenames, path_to_solve_field, path_to_netpbm)
    
    return None


if __name__=="__main__":
    main()
