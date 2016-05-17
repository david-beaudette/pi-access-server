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

# Load configuration    
db_config_file = 'db_connect_fields.ignored'

commutators = []
members = []
memberships = []
cards = []
tags = []
db_connect.read_db(commutators, members, memberships, cards, tags, db_config_file)
csv_filename = 'access_tables.csv'
logging.info('Writing access tables to file.')
csv_rw.member_access_write(csv_filename,
                           commutators,
                           members,
                           memberships,
                           cards,
                           tags)


# Load tables from file
commutators_csv = []
cards_csv = []
members_csv = []
memberships_csv = []
authorisations_csv = []
csv_rw.member_access_read('access_tables.csv', commutators_csv,
                          members_csv, memberships_csv, cards_csv, authorisations_csv)
                          
event_list = []

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
    file_template = args.log_dir + os.sep + 'events_*.csv'
    print("Looking for %s." % file_template)
    event_file_list = glob(file_template)
    
    for event_file in event_file_list:
        get_first_confirmed_cards(event_file)
    
    print(event_list)
    
    with open('event_list.csv', 'wb') as csvfile:
        infowriter = csv.writer(csvfile, delimiter=';')
        infowriter.writerows(event_list)
        
def process_log(args):
    """
    Analyse one log.
    """
    get_first_confirmed_cards(args.log_file)
    
def get_first_confirmed_cards(events_filename):
    """
    Analyse one log.
    """
    
    # Open file
    with open(events_filename, 'r') as csvfile:
        eventreader = csv.reader(csvfile, delimiter=';')
    
        # For all entries
        for event in eventreader:
        
            # Get timestamp, event type and member
            if (event[1] == '0x31' or event[1] == '0x33') and not card_in_list(event[2]):
            # If event type is "Confirmed" and member is not already included in list
                #print("%s with card %s." % (event[3], event[2]))
                
                # Get membership 
                membership_type = get_membership(event[2])
                                
                # Add time, member, database ID and membership type to analysis output 
                event_list.append([event[0], event[3], event[2], membership_type])
    
    

def get_membership(card):
    """
    Retrieve the membership for the given card.
    """
    membership_type = 0
    for member_num in range(len(members_csv)):
        #print(cards_csv[member_num])
        if cards_csv[member_num] == card:
            member_name = members_csv[member_num]
            membership_type = memberships_csv[member_num]
            #print("Found %s member with membership %s from card %s" % (member_name, membership_type, card))
            
    if membership_type == 0:
        print("Warning: No member found with card %s." % card)
        
    return membership_type

def card_in_list(card):
    """
    Check if a card is already in event list.
    """
    for event_num in range(len(event_list)):
        if event_list[event_num][2] == card:
          return True
          
    return False
    
    
if __name__ == '__main__':
    # Create the top-level parser
    parser = argparse.ArgumentParser(version='1.0', description='Commutator log analysis.')    
    subparsers = parser.add_subparsers()
    
    # Create subcommand parsers
    parser_sdr = subparsers.add_parser('append_data', description='Retrieves access tables from the database.')
    parser_sdr.set_defaults(func=append_data)
        
    parser_sdr = subparsers.add_parser('process_log', description='Processes one log file.')
    parser_sdr.add_argument('-i', '--log_file', help='Name of the commutator log csv file.')
    parser_sdr.set_defaults(func=process_log)
        
    parser_sdr = subparsers.add_parser('process_all_logs', description='Processes all log files.')
    parser_sdr.add_argument('-d', '--log_dir', help='Folder containing the commutator log csv files.')
    parser_sdr.set_defaults(func=process_all_logs)
        
    args = parser.parse_args()
    
    # Execute required function 
    args.func(args)

        
        
