#!/usr/bin/python
#
# astrometrica-gen.py
#
# Authors:
#   Philipp v. Bieberstein (pbieberstein@email.arizona.edu)
#   Matt Madrid (matthewmadrid@email.arizona.edu)
#   David Sidi (dsidi@email.arizona.edu)
#   Adam Soll (adamsoll@email.arizona.edu)
"""

"""


def build_dataframe():
    """
    """
    pass


def passes_master():
    """
    """
    pass


def solve_field():
    """
    """
    # FITS files that fail solve_field should be added to secondary list for logging
    pass


def generate_astro_config():
    """
    """
    pass


if __name__=="__main__":
    unprocessed_fits = []
    new_frame = build_dataframe(unprocessed_fits)
    filtered_frame = passes_master(new_frame)
    modified_fits = solve_field(filtered_frame)
    generate_astro_config(modified_fits)