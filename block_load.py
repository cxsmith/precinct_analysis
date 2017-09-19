from py2casefold import casefold
import argparse
import csv
from osgeo import ogr

def get_blocks(state, county, census_path):
    # Clean up the args since they're typed by the user:
    if len(state) > 2:
        state = state[:2]
    state = state.lower()

    if census_path.endswith("/"):
        census_path = census_path[:-1]

    # Format for census text file lookup:
    county = county + " County" if not county.endswith(" County") else county
    # Look it up:
    county_codes = open("%s/%s/county_codes.txt" % (census_path, state), "r")
    if county_codes is None:
        print("Error, could not find county list.  Make sure your path to the census information is correct.")
        print("And make sure that your census directory is formatted correctly.")
        return None

    county_csv = csv.reader(county_codes)

    county_code = None
    state_code = None
    for row in county_csv:
        if row[3].lower() == county.lower():
            county_code = row[2]
            state_code = row[1]

    if county_code is None:
        print("County code for %s not found!  Exiting" % county)
        return None

    return state_code, county_code, ogr.Open("%s/%s/tl_2015_%s_tabblock10.shp" % (census_path, state, state_code)), ogr.Open("%s/%s/tl_2015_%s_tabblock10.dbf" % (census_path, state, state_code))
