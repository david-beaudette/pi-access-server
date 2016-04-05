#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# The commutator logs analysis script
#

# Import Python modules
import sys
import ConfigParser
from time import strftime, sleep
import logging
import argparse
from glob import glob
import shutil
import os
import socket
import csv

# Import project modules
import db_connect
import csv_rw

# Main commands
def append_data(args):
    """
    Append data from one file to analysis output file.
    """
    # Open analysis file 
    
    # Get last data timestamp
    
    # Find all files generated later
    
    # Analyse these files
    
    # Append results to analysis file
    
    pass
    
def generate_analysis_file(args):
    """
    Create a new analysis output file.
    """
    pass
    
def process_all_logs(args):
    """
    Analyse all logs from a given folder.
    """
    pass
    
def process_log(args):
    """
    Analyse one log.
    """
    
    # Open file
    
    # For all entries
    
        # Get timestamp, event type and member
        
        # If event type is "Confirmed" and member is not already include in list
        
            # Get membership 
            
            # Add time, member, database ID and membership type to analysis output 
    
    pass

    
if __name__ == '__main__':
    # Create the top-level parser
    parser = argparse.ArgumentParser(version='1.0', description='Commutator log analysis.')    
    subparsers = parser.add_subparsers()
    
    # Create subcommand parsers
    parser_sdr = subparsers.add_parser('append_data', description='Retrieves access tables from the database.')
    parser_sdr.set_defaults(func=append_data)
        
    args = parser.parse_args()
    
    # Execute required function 
    args.func(args)

        
        
