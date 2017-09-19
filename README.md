# precinct_analysis

These are a bunch of GDAL python scripts I wrote for a politial campaign.

## Source data

Scripts reference a bunch of .shp files that contain census blocks.  Since these
files are hundreds of megabytes, I am refraining from adding them to the
repository.  They can be found at http://census.gov

Their structure in the census blocks directory is:

directory/(two letter state code)/shapefiles

## Dependencies

This repo uses the osgeo python library, which depends on having an
installation of libgdal already.  You won't be able to install the python
package "GDAL" without already having "libgdal" installed on your OS.  For
example:

sudo apt install libgdal-dev

as a prerequisite.  Unfortunately, the version of libgdal in your package
manager may not match the version of GDAL that pip wants to install.  To remedy
this, you can check your OS's GDAL version like so:

gdal-config --version

and download the appropriate version, eg:

pip install GDAL==$(gdal-config --version | awk -F'[.]' '{print $1"."$2}') 

credit: https://stackoverflow.com/questions/38630474/error-while-installing-gdal
