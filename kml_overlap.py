"""This python script will calculate the overlap between a precinct and its
census blocks.  Since there are fewer precincts than census blocks, I anticipate
that precincts will contain blocks.  If there's only partial overlap, then the
percent area of the census block contained within the precinct will be noted."""

import block_load
import csv
import argparse
import sys
import pdb
import traceback
from pprint import pprint

print("Importing GIS libraries") # osgeo takes a while, so give user feedback

from pykml import parser
from osgeo import ogr


def read_layer(layer):
    """Iterator to get all the features from a layer."""
    feature = layer.GetNextFeature()

    while feature:
        yield feature
        feature = layer.GetNextFeature()

    raise StopIteration

def match(feature, blocks):
    """This function does the heavy lifting for calculating overlap. Accepts
    a parent precinct feature to find which census blocks are in it. Blocks
    is a dict of census block names to census block feature objects. Geometries
    are extracted in this function so the feature object is still in memory
    when the geometry is, preventing a segfault.

    Returns a map of block names to what percentage of their area is enclosed
    in the given precinct.
    """
    current = {}
    precinct_geom = feature.GetGeometryRef()

    try:
        to_remove = []
        i = 0
        for name, block in blocks.items():
            block_geom = block.GetGeometryRef()

            # Overlapping and containing are mutually exclusive, so check both.
            if (precinct_geom.Overlaps(block_geom) or
                    precinct_geom.Contains(block_geom)):
                if precinct_geom.Contains(block_geom):
                    current[name] = 1.0
                    to_remove.append(name)
                    continue
                geo = precinct_geom.Intersection(block_geom)
                overlap_fraction = geo.GetArea() / block_geom.GetArea()
                if overlap_fraction < 0.01:
                    pass
                elif overlap_fraction > 0.99:
                    current[name] = 1.0
                    to_remove.append(name)
                else:
                    current[name] = overlap_fraction
        for rm in to_remove:
            del blocks[rm]
    except AttributeError:
        print("error?")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback)

    return current

arg_parser = argparse.ArgumentParser(description='Map county precincts to census blocks.')
arg_parser.add_argument('--state',
    type=str,
    nargs="?",
    default="wa",
    help="The state of the county you want to make a map of.  Please use two-letter code.  Default is Washington state.")
arg_parser.add_argument('--county',
    type=str,
    nargs="?",
    default="king",
    help="The county you want to make a map of.  Default is King county")
arg_parser.add_argument('--census_path',
    type=str,
    nargs="?",
    default="census_blocks",
    help="The path to the directory with all census block information.")
arg_parser.add_argument('--precinct_kml',
    type=str,
    nargs=1,
    help="The KML file that defines the precincts to calculate the overlaps of.")

args = arg_parser.parse_args()

state_code, county_code, census_blocks, dbf_blocks = block_load.get_blocks(args.state, args.county, args.census_path)

if not census_blocks:
    print("Error, can't find census information.")
    sys.exit(1)

driver = ogr.GetDriverByName("KML")
precinct_src = driver.Open(args.precinct_kml[0])

if not precinct_src:
    print("Error, can't find precinct information file %s" %
        args.precinct_kml[0])
    sys.exit(1)

layer = census_blocks.GetLayer(0)
total_blocks = layer.GetFeatureCount()

# Change the census blocks from strings to primitives:
block_dict = {}

print( "county code: " + county_code)

# Can't copy only the GetGeometryRef because the underlying feature needs to
# stay alive for later, see: 
# https://gis.stackexchange.com/questions/126298/how-to-copy-a-geometry-with-python-ogr
blocks = {block.GetField(4): block
                for block in read_layer(layer)
                   if block.GetField(1) == county_code}

precinct_map = {}

print("Matching precincts to census blocks")

layer = precinct_src.GetLayer(0)

total_pres = layer.GetFeatureCount()
for precinct in read_layer(layer):
    name = precinct.GetField(0)
    print("Looking at %s matching %d blocks" % (name, len(blocks)))
    precinct_map[name] = match(precinct, blocks)

print ("%d census blocks were not engulfed." % len(blocks))
print ("It's OK and expected for this number to be non-zero, but I'd expect it to be under about %d or so." % (total_blocks/5))
print ("Blocks processed!  Sanity checking.")

aggregate_coverage = {}
for assigned_blocks in precinct_map.values():
    for block, coverage in assigned_blocks.items():
        if block in aggregate_coverage.keys():
            aggregate_coverage[block] += coverage
        else:
            aggregate_coverage[block] = coverage

suspicious_precincts = [suspicious for suspicious in aggregate_coverage.items() if suspicious[1] > 1.1]
if suspicious_precincts:
    pprint(suspicious_precincts)

out = open("map.csv", "w")

for k, v in precinct_map.items():
    out.write("%s, %s\n" % (k, ",".join(["(%s %f)" % (name, area_fraction) for name, area_fraction in v.items()])))
out.close()
