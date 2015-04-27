#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# The server main program
#

import sys
import ConfigParser
from time import strftime
import logging
import argparse
from glob import glob
import shutil
import os

import db_connect
import link_command
import csv_rw

def server_db_retrieve(args):
    print('Retrieving tables from database.')
    machines = []
    members = []
    cards = []
    tags = []
    
    # Test db data retrieval
    config_filename = 'db_connect_fields.ignored'
    db_connect.read_db(machines, members, cards, tags, config_filename)
    csv_filename = 'access_tables.csv'
    print('Writing access tables to file.')
    csv_rw.member_access_write(csv_filename,
                               machines,
                               members,
                               cards,
                               tags)
    print('Access tables were written to %s.' % csv_filename)

def server_new_log(args):
    print('Starting a new software events log file.')
    # Find existing log
    log_file = glob('piaccessserver_*.log')
    logging.shutdown()
    if len(log_file) > 0:
        archive_folder_name = 'archives'
        print('Archiving %s file in folder %s.' % (log_file[0], archive_folder_name))
        if not os.path.exists(archive_folder_name):
            os.makedirs(archive_folder_name)
        shutil.move(log_file[0], archive_folder_name + os.path.sep + log_file[0])
    # Create another log file
    log_file = get_sw_log_filename()
    print('Created new %s file.' % log_file[0])
    logging.basicConfig(filename=log_file[0],
                        format='%(asctime)s:%(levelname)s:%(message)s',
                        level=logging.DEBUG)
    logging.info('Software events log file creation.')
    
def commutator_check(args):
    print('Commutator %s is fine.' % args.commutator_name)

def commutator_update(args):
    print('Commutator %s access tables were updated.' % args.commutator_name)

def commutator_on(args):
    print('Commutator %s is now always on.' % args.commutator_name)

def commutator_off(args):
    print('Commutator %s is now always off.' % args.commutator_name)

def commutator_auto(args):
    print('Commutator %s now activates using cards and access tables.' % args.commutator_name)

def commutator_get_log(args):
    print('Commutator %s logs were retrieved.' % args.commutator_name)

def commutator_new_log(args):
    print('Commutator %s logs will be saved in a new file.' % args.commutator_name)

def get_sw_log_filename():
    log_file = glob('piaccessserver_*.log')
    if len(log_file) == 0:
        # Create file with current time
        log_file.append('piaccessserver_' + strftime("%Y-%m-%d_%Hh%Mm%Ss") + '.log')
    return log_file   

if __name__ == '__main__':
    # Set software event logging
    log_file = get_sw_log_filename()
    logging.basicConfig(filename=log_file[0],
                        format='%(asctime)s:%(levelname)s:%(message)s',
                        level=logging.DEBUG)
    
    # Create the top-level parser
    parser = argparse.ArgumentParser(version='1.0', description='Access server software for managing RFID commutators.')    
    subparsers = parser.add_subparsers()
    
    # Create subcommand parsers
    parser_sdr = subparsers.add_parser('server_db_retrieve', description='Retrieves access tables from the database.')
    parser_sdr.set_defaults(func=server_db_retrieve)

    parser_sdr = subparsers.add_parser('server_new_log', description='Backups current server software events log and starts a new one with the current date.')
    parser_sdr.set_defaults(func=server_new_log)

    commutator_name_help = 'Name of the commutator as defined in the configuration file (default is all commutators).'    
    parser_sdr = subparsers.add_parser('commutator_check', description='Backups current server software events log and starts a new one with the current date.')
    parser_sdr.add_argument('-n', '--commutator_name', default='all', help=commutator_name_help)
    parser_sdr.set_defaults(func=commutator_check)
        
    parser_sdr = subparsers.add_parser('commutator_update', description='Updates the access tables of a commutator.')
    parser_sdr.add_argument('-n', '--commutator_name', default='all', help=commutator_name_help)
    parser_sdr.set_defaults(func=commutator_update)
        
    parser_sdr = subparsers.add_parser('commutator_on', description='Sets commutator as always on.')
    parser_sdr.add_argument('-n', '--commutator_name', default='all', help=commutator_name_help)
    parser_sdr.set_defaults(func=commutator_on)
        
    parser_sdr = subparsers.add_parser('commutator_off', description='Sets commutator as always off.')
    parser_sdr.add_argument('-n', '--commutator_name', default='all', help=commutator_name_help)
    parser_sdr.set_defaults(func=commutator_off)
        
    parser_sdr = subparsers.add_parser('commutator_auto', description='Sets commutator activation to automatic (using card reader and access tables).')
    parser_sdr.add_argument('-n', '--commutator_name', default='all', help=commutator_name_help)
    parser_sdr.set_defaults(func=commutator_auto)
        
    parser_sdr = subparsers.add_parser('commutator_get_log', description='Gets commutator events log.')
    parser_sdr.add_argument('-n', '--commutator_name', default='all', help=commutator_name_help)
    parser_sdr.set_defaults(func=commutator_get_log)
        
    parser_sdr = subparsers.add_parser('commutator_new_log', description='Backups current commutator events log and starts a new one with the current date.')
    parser_sdr.add_argument('-n', '--commutator_name', default='all', help=commutator_name_help)
    parser_sdr.set_defaults(func=commutator_new_log)
        
    args = parser.parse_args()
    args.func(args)

        
        
