# useful functions for the package

import argparse
import csv
import datetime
import os
import urllib.request

MIN_VAL = 0
MAX_VAL = 1

def range_limited_float_type(arg):
    """Type function for argparse - a float within some predefined bounds

    Args:
        arg: argparse argument 
    """
    try:
        f = float(arg)
    except ValueError:    
        raise argparse.ArgumentTypeError("Must be a floating point number")
    if f < MIN_VAL or f > MAX_VAL:
        raise argparse.ArgumentTypeError("Argument must be < " + str(MAX_VAL) + " and > " + str(MIN_VAL))
    return f

def is_valid_path(filepath):
    """Return True if filepath is valid
    
    Args:
        filepath (str): path to file
    
    Returns:
        bool: True if path exists, False otherwise
    """
    if filepath and not os.access(filepath, os.W_OK):
        try:
            open(filepath, 'w').close()
            os.unlink(filepath)
            return True
        except OSError:
            return False
    else:  # path is accessible
        return True


def is_valid_file(filepath):
    """Return True if filepath exists
    Args:
        filepath (str): path to file
    Returns:
        bool: True if path exists, False otherwise
    """
    try:
        open(filepath, 'r').close()
        return True
    except OSError:
        return False


def is_valid_dir(dirpath):
    """Return True if directory exists or can be created (then create it)
    
    Args:
        dirpath (str): path of directory
    Returns:
        bool: True if dir exists, False otherwise
    """
    if not os.path.isdir(dirpath):
        try:
            os.makedirs(dirpath)
            return True
        except OSError:
            return False
    else:
        return True

def get_rest_uniprot_release():
    """Get the release version and date of Uniprot and Trembl and also the date of the query.

    Returns:
        dict: metadata of Uniprot release
    """
    uniprot_releases = {}

    # Get Uniprot release version
    uniprot_response = urllib.request.urlopen('https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/reldate.txt')
    uniprot_lines = uniprot_response.readlines()
    uniprot_release_number = uniprot_lines[0].decode('utf-8').split(' ')[3].replace('\n','')
    swissprot_release_number = uniprot_lines[1].decode('utf-8').split(' ')[2].replace('\n','')
    swissprot_release_date = uniprot_lines[1].decode('utf-8').split(' ')[4].replace('\n','')
    trembl_release_number = uniprot_lines[2].decode('utf-8').split(' ')[2].replace('\n','')
    trembl_release_date = uniprot_lines[2].decode('utf-8').split(' ')[4].replace('\n','')

    date = datetime.datetime.now().strftime('%d-%B-%Y %H:%M:%S')

    uniprot_releases['esmecata_query_system'] = 'REST queries on Uniprot'
    uniprot_releases['uniprot_release'] = uniprot_release_number
    uniprot_releases['access_time'] = date
    uniprot_releases['swissprot_release_number'] = swissprot_release_number
    uniprot_releases['swissprot_release_date'] = swissprot_release_date
    uniprot_releases['trembl_release_number'] = trembl_release_number
    uniprot_releases['trembl_release_date'] = trembl_release_date

    return uniprot_releases


def get_sparql_uniprot_release(uniprot_sparql_endpoint):
    """Get the release version and date of Uniprot and Trembl and also the date of the query.

    Returns:
        dict: metadata of Uniprot release
    """
    from SPARQLWrapper import SPARQLWrapper, TSV
    from io import StringIO
    uniprot_releases = {}

    sparql = SPARQLWrapper(uniprot_sparql_endpoint)

    uniprot_sparql_query = """SELECT ?version
    WHERE
    {{
        [] <http://purl.org/pav/2.0/version> ?version .
    }}
    """

    sparql.setQuery(uniprot_sparql_query)
    # Parse output.
    sparql.setReturnFormat(TSV)
    results = sparql.query().convert().decode('utf-8')
    csvreader = csv.reader(StringIO(results), delimiter='\t')
    # Avoid header.
    next(csvreader)
    results = {}
    uniprot_release_number = [line[0] for line in csvreader][0]
    date = datetime.datetime.now().strftime('%d-%B-%Y %H:%M:%S')

    uniprot_releases['esmecata_query_system'] = 'SPARQL queries'
    uniprot_releases['esmecata_sparql_endpoint'] = uniprot_sparql_endpoint
    uniprot_releases['uniprot_release'] = uniprot_release_number
    uniprot_releases['access_time'] = date

    return uniprot_releases
