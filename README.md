# astrogen
A program to modify FITS file metadata for the purpose of generating Astrometrica compatible configuration files. 

## Requirements
* Python 2.7 + click
* Working solve-field from astronomy.net on your path
* pyfits

## How to run
An easy way to see the functioning of the program is to run the _test_solve_astrometry unit test. This takes the batch of FITS files in the tests/fits_files directory and generates a makeflow script, runs that script on the compute nodes, extracts parameters from the results of that run and finally deposits the output in the subdirectories of output.

## How it works
The user edits a file to configure parameters. One of these are iPlant credentials: FITS files are retrieved from iPlant in batches. Makeflows are generated for each batch, and submitted to workers via pbs_submit_workers. These workers run solve-field to solve the astrometry of the images. Once a batch has completed, the original fits file is modified in its headers and a configuration file for Astrometrica is produced, and placed in the output directory.
