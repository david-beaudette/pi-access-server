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
import socket

import db_connect
import link_command
import csv_rw

# Main commands
def server_db_retrieve(args = []):
    """
    Retrieves the access tables from the database.
    """
    logging.info('Retrieving tables from database.')
    commutators = []
    members = []
    cards = []
    tags = []
    
    # Test db data retrieval
    config = get_server_config()
    db_config_file = config.get('DATABASE', 'db_config_file')
    db_connect.read_db(commutators, members, cards, tags, db_config_file)
    csv_filename = 'access_tables.csv'
    logging.info('Writing access tables to file.')
    csv_rw.member_access_write(csv_filename,
                               commutators,
                               members,
                               cards,
                               tags)
    logging.info('Access tables were written to %s.' % csv_filename)


def server_new_log(args):
    """
    Archives the current software event log, if any, and creates a new timestamped log.
    """
    print('Starting a new software events log file.')
    # Find existing log
    log_file = glob('piaccessserver_*.log')
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
                        format='%(asctime)s:%(levelname)s:%(funcName)s:%(message)s',
                        level=logging.DEBUG)
    logging.info('Software events log file creation.')
    
def commutator_check(args):
    send_commutator_command(args.commutator_name, 'check')
                
def commutator_update(args):
    """Updates the access tables of one or all the commutators."""
    # Check if a table is available
    csv_filename = glob('access_tables.csv')
    if len(csv_filename) == 0:
        # Generate access table file
        server_db_retrieve(args)
        
    # Load tables from file
    commutators = []
    cards = []
    authorisations = []
    csv_rw.member_access_read('access_tables.csv', commutators,
                              cards, authorisations)
    
    # Load config file
    config = get_server_config()
    
    # Generate commutator list
    if(args.commutator_name != 'all'):      
        index = commutators.index(args.commutator_name)
        commutators = [commutators[index]]
        authorisations = [authorisations[index]]
      
    # Update commutators
    for index, commutator in enumerate(commutators):
        if config.has_section(commutator):
            # Load radio parameters from config file
            channel = config.getint(commutator, 'channel')
            commutator_id = config.getint(commutator, 'id')
            # Create a link for this commutator
            print('Would create a link to %s (id = %d) on channel %d.' % (commutator, commutator_id, channel))
            #link = LinkCommand(radio, channel,
            #                   commutator_id, commutator))
            print [cards, authorisations[index]]
            #status = link.update_table([cards, authorisations[index]])
            
    # Generate commutator list
    if(args.commutator_name == 'all'):      
      logging.info('The access tables of all %0.0f commutators were updated.' % len(commutators))
    else:
      logging.info('The access tables of commutator %s were updated.' % args.commutator_name)
      
def commutator_on(args):
    send_commutator_command(args.commutator_name, 'on')

def commutator_off(args):
    send_commutator_command(args.commutator_name, 'off')

def commutator_auto(args):
    send_commutator_command(args.commutator_name, 'auto')

def commutator_get_log(args):
    logging.info('Commutator %s logs were retrieved.' % args.commutator_name)

def commutator_new_log(args):
    """
    Archives the commutator event log file, if any, and starts a new timestamped log. If 
    the name if the commutator is provided, only affects this commutator's event log file.
    """
    if(args.commutator_name == 'all'):      
      # Get commutator names from server
      commutators = get_commutators()
      logging.info('The event log files of all %0.0f commutators will be saved to new files.' % len(commutators))
    else:
      logging.info('The event log file of commutator %s will be saved to a new file.' % args.commutator_name)
      commutators = [args.commutator_name]
      
    archive_folder_name = 'archives'
    for commutator in commutators:
      log_file = glob('events_' + commutator + '_*.log')
      if len(log_file) > 0:
          if not os.path.exists(archive_folder_name):
              os.makedirs(archive_folder_name)
          shutil.move(log_file[0], archive_folder_name + os.path.sep + log_file[0])
          logging.info('Archived %s file in folder %s.' % (log_file[0], archive_folder_name))
      # Create another log file
      log_file = 'events_' + commutator + '_' + strftime("%Y-%m-%d_%Hh%Mm%Ss") + '.log'
      open(log_file, 'a').close()
      logging.info('Created new commutator events log file %s.' % log_file)
     
# Support functions
def get_sw_log_filename():
    log_file = glob('piaccessserver_*.log')
    if len(log_file) == 0:
        # Create file with current time
        log_file.append('piaccessserver_' + strftime("%Y-%m-%d_%Hh%Mm%Ss") + '.log')
    return log_file

def get_commutator_log_filename():
    log_file = glob('events_' + commutator + '_*.log')
    if len(log_file) == 0:
        # Create file with current time
        log_file.append('events_' + commutator + '_' + strftime("%Y-%m-%d_%Hh%Mm%Ss") + '.log')
        open(log_file, 'a').close()
    return log_file

def get_server_config():    
    config_filename = 'piaccessserver.ini'
    config = ConfigParser.RawConfigParser()    
    config.read(config_filename)
    return config

def get_commutators():
    config = get_server_config()
    
    # Check if a table is available
    csv_filename = glob('access_tables.csv')
    if len(csv_filename) == 0:
        # Generate access table file
        server_db_retrieve(args)
        
    # Load tables from file
    commutators = []
    csv_rw.member_access_read('access_tables.csv', commutators, [], [])

    for commutator in commutators:
      # Find section in config file
      if config.has_section(commutator[1]):
          commutators.append(commutator[1])
      
    return commutators

def send_commutator_command(commutator_name, command_name):    
    # Load config file
    config = get_server_config()
    
    if(commutator_name == 'all'):      
      # Get commutator names from server
      commutators = get_commutators()
    else:
      commutators = [commutator_name]
      
    # Update commutators
    for index, commutator in enumerate(commutators):
        if config.has_section(commutator):
            # Load radio parameters from config file
            channel = config.getint(commutator, 'channel')
            commutator_id = config.getint(commutator, 'id')
            # Create a link for this commutator
            print('Would create a link to %s (id = %d) on channel %d.' % (commutator, commutator_id, channel))
            #link = LinkCommand(radio, channel,
            #                   commutator_id, commutator))
            status = {"commutator_ok": True}
            if command_name == 'check':
                #status = link.auto()
                if status["commutator_ok"]:
                    print('Commutator %s is functional.' % commutator)
                    logging.info('Commutator %s is functional.' % commutator)
            elif command_name == 'auto':
                #status = link.auto()
                if status["commutator_ok"]:
                    print('Commutator %s set to automatic mode.' % commutator)
                    logging.info('Commutator %s set to automatic mode.' % commutator)
            elif command_name == 'on':
                #status = link.enable_commutator()
                if status["commutator_ok"]:
                    print('Commutator %s set to always on mode.' % commutator)
                    logging.info('Commutator %s set to always on mode.' % commutator)
            elif command_name == 'off':
                #status = link.disable_commutator()
                if status["commutator_ok"]:
                    print('Commutator %s set to always off mode.' % commutator)
                    logging.info('Commutator %s set to always off mode.' % commutator)
              

    
if __name__ == '__main__':
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
    
    # Set software event logging
    args_vars = vars(args)
    if(args_vars['func'].__name__ != 'server_new_log'):
      log_file = get_sw_log_filename()
      logging.basicConfig(filename=log_file[0],
                          format='%(asctime)s:%(levelname)s:%(funcName)s:%(message)s',
                          level=logging.DEBUG)
    
    # Execute required function 
    args.func(args)

        
        
