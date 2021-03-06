#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# The server main program
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
from link_command import LinkCommand
import csv_rw

# Configure GPIO and SPI
import RPi.GPIO as GPIO
import spidev
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Load configuration    
config_filename = 'piaccessserver.ini'
config = ConfigParser.RawConfigParser()    
config.read(config_filename)

# Configure radio
from lib_nrf24 import NRF24
w_pipe = [0xF0, 0xF0, 0xF0, 0xF0, 0xE1]
r_pipe = [0xF0, 0xF0, 0xF0, 0xF0, 0xD2]

radio = NRF24(GPIO, spidev.SpiDev())

# Use configuration file parameter values to setup radio
radio.begin(0, 25)
#sleep(1)
# setRetries(delay, count) -> both between 0 and 15
radio.setRetries(15,15)
radio.setPayloadSize(12)
radio.setDataRate(NRF24.BR_1MBPS)
radio.setPALevel(NRF24.PA_MAX)
radio.setAutoAck(True)
radio.enableDynamicPayloads()

radio.openWritingPipe(w_pipe)
radio.openReadingPipe(1, r_pipe)

#radio.printDetails()

# Main commands
def server_db_retrieve(args = []):
    """
    Retrieves the access tables from the database.
    """
    logging.info('Retrieving tables from database.')
    commutators = []
    members = []
    memberships = []
    cards = []
    tags = []
    
    # Test db data retrieval
    db_config_file = config.get('DATABASE', 'db_config_file')
    db_connect.read_db(commutators, members, memberships, cards, tags, db_config_file)
    csv_filename = 'access_tables.csv'
    logging.info('Writing access tables to file.')
    csv_rw.member_access_write(csv_filename,
                               commutators,
                               members,
                               memberships,
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
            os.chmod(archive_folder_name, 0o777)
        shutil.move(log_file[0], archive_folder_name + os.path.sep + log_file[0])
    # Create another log file
    log_file = get_sw_log_filename()
    print('Created new %s file.' % log_file[0])
    logging.basicConfig(filename=log_file[0],
                        format='%(asctime)s:%(levelname)s:%(funcName)s:%(message)s',
                        level=logging.DEBUG)
    os.chmod(log_file[0], 0o777)
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
    members = []
    memberships = []
    authorisations = []
    csv_rw.member_access_read('access_tables.csv', commutators,
                              members, memberships, cards, authorisations)
    
    # Consider access tags or not
    if not config.getboolean('ACCESS_SERVER', 'manage_tags'):
        # Set all authorisations to valid, whatever tag was assigned to the member
        for i in range(len(authorisations)):
            for j in range(len(authorisations[i])):
                authorisations[i][j] = True
                
    # Manage membership validity                
    if config.getboolean('ACCESS_SERVER', 'manage_membership'):
        # Valid authorisations depend on membership validity
        for i in range(len(authorisations)):
            for j in range(len(authorisations[i])):
                authorisations[i][j] = authorisations[i][j] and (memberships[j] > 0) 
                #logging.debug('User %s (membership = %d), commutator %s, tag validity = %d.' % (members[j], memberships[j], commutators[i], authorisations[i][j]))
                
    # Generate commutator list
    if(args.commutator_name != 'all'):      
        comm_num = commutators.index(args.commutator_name)
        commutators = [commutators[comm_num]]
        authorisations = [authorisations[comm_num]]
      
    # Update commutators
    num_commutators = 0
    for index, commutator in enumerate(commutators):
        if config.has_section(commutator):
            # Load radio parameters from config file
            channel = config.getint(commutator, 'channel')
            commutator_id = config.getint(commutator, 'id')
            # Create a link for this commutator
            #print('Creating a link to %s (id = %d) on channel %d.' % (commutator, commutator_id, channel))
            link = LinkCommand(radio, channel,
                               commutator_id, commutator)
            #print [cards, authorisations[index]]
            status = link.update_table([cards, authorisations[index]])
            num_commutators = num_commutators + 1
            
    # Display result
    if(args.commutator_name == 'all'):      
      logging.info('The access tables of all %0.0f commutators were updated.' % num_commutators)
    else:
      logging.info('The access tables of commutator %s were updated.' % args.commutator_name)
      
def commutator_on(args):
    send_commutator_command(args.commutator_name, 'on')

def commutator_off(args):
    send_commutator_command(args.commutator_name, 'off')

def commutator_auto(args):
    send_commutator_command(args.commutator_name, 'auto')

def commutator_clear_memory(args):
    send_commutator_command(args.commutator_name, 'clear_memory')

def commutator_single_activation(args):
    send_commutator_command(args.commutator_name, 'single_activation')

def commutator_double_activation(args):
    send_commutator_command(args.commutator_name, 'double_activation')
    
def commutator_check_memory(args):
    send_commutator_command(args.commutator_name, 'check_memory')

def commutator_get_log(args):    
    # Define event names
    event_strings = {'0x00':'Error'}
    event_strings['0x30'] = 'Un 1er membre autorisé a utilisé sa carte en mode double autorisation.'
    event_strings['0x31'] = 'Un membre autorisé a activé le commutateur.'
    event_strings['0x32'] = 'Un membre autorisé a désactivé le commutateur.'
    event_strings['0x33'] = 'Un membre non autorisé a utilisé sa carte.'
    event_strings['0x34'] = 'Une carte inconnue a été détectée.'
    
    # Generate commutator list
    if(args.commutator_name == 'all'):      
      # Get commutator names from server
      commutators = get_commutators()
    else:
      commutators = [args.commutator_name]
      
    # Check if a table is available
    csv_filename = glob('access_tables.csv')
    if len(csv_filename) == 0:
        # Generate access table file
        server_db_retrieve(args)
        
    # Load tables from file
    commutators_csv = []
    cards_csv = []
    members_csv = []
    memberships_csv = []
    authorisations_csv = []
    csv_rw.member_access_read('access_tables.csv', commutators_csv,
                              members_csv, memberships_csv, cards_csv, authorisations_csv)
                              
    # Update commutators
    for index, commutator in enumerate(commutators):
        if config.has_section(commutator):
            # Load radio parameters from config file
            channel = config.getint(commutator, 'channel')
            commutator_id = config.getint(commutator, 'id')
            # Create a link for this commutator
            #print('Creating a link to %s (id = %d) on channel %d.' % (commutator, commutator_id, channel))
            link = LinkCommand(radio, channel,
                               commutator_id, commutator)            
            status = link.dump_logging()
            
            # Write events to log file
            filename = get_commutator_log_filename(commutator)
            with open(filename, 'ab') as csvfile:
                log_file = csv.writer(csvfile, delimiter=';',
                                        quotechar='"', quoting=csv.QUOTE_MINIMAL)
                for event_num in range(status['log_count']):
                    # Compute card code from individual bytes
                    card_hex_code = hex(0x01000000 * status["log_users"][event_num][0] + 
                                        0x00010000 * status["log_users"][event_num][1] + 
                                        0x00000100 * status["log_users"][event_num][2] + 
                                        status["log_users"][event_num][3])
                    card_hex_code = card_hex_code[2:10].upper()
                    # Find card code in database card list
                    member_name = 'Unknown'
                    membership_type = 0
                    for member_num in range(len(members_csv)):
                        if cards_csv[member_num] == card_hex_code:
                            member_name = members_csv[member_num]
                            membership_type = memberships_csv[member_num]
                                                     
                    print(hex(status["log_codes"][event_num]))
                    print(event_strings[hex(status["log_codes"][event_num])])
                    log_file.writerow((status['log_times'][event_num].strftime("%Y-%m-%d %H:%M:%S"),
                                      hex(status["log_codes"][event_num]),
                                      card_hex_code, member_name, membership_type, 
                                      event_strings[hex(status["log_codes"][event_num])]))            
            os.chmod(filename, 0o777)
    # Display result
    if(args.commutator_name == 'all'):      
      logging.info('The logged events of all %0.0f commutators were retrieved.' % len(commutators))
    else:
      logging.info('The logged events of commutator %s were retrieved.' % args.commutator_name)

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
      log_file = glob('events_' + commutator + '_*.csv')
      if len(log_file) > 0:
          if not os.path.exists(archive_folder_name):
              os.makedirs(archive_folder_name)
              os.chmod(archive_folder_name, 0o777)
          shutil.move(log_file[0], archive_folder_name + os.path.sep + log_file[0])
          logging.info('Archived %s file in folder %s.' % (log_file[0], archive_folder_name))
      # Create another log file
      log_file = 'events_' + commutator + '_' + strftime("%Y-%m-%d_%Hh%Mm%Ss") + '.csv'
      open(log_file, 'a').close()
      os.chmod(log_file, 0o777)
      logging.info('Created new commutator events log file %s.' % log_file)
     
# Support functions
def get_sw_log_filename():
    log_file = glob('piaccessserver_*.log')
    if len(log_file) == 0:
        # Create file with current time
        log_file.append('piaccessserver_' + strftime("%Y-%m-%d_%Hh%Mm%Ss") + '.log')
    return log_file

def get_commutator_log_filename(commutator_name):
    log_file = glob('events_' + commutator_name + '_*.csv')
    if len(log_file) == 0:
        # Create file with current time
        log_file.append('events_' + commutator_name + '_' + strftime("%Y-%m-%d_%Hh%Mm%Ss") + '.csv')
        open(log_file[0], 'a').close()
        os.chmod(log_file[0], 0o777)
    return log_file[0]

def get_commutators():
    # Check if a table is available
    csv_filename = glob('access_tables.csv')
    if len(csv_filename) == 0:
        # Generate access table file
        server_db_retrieve(args)
        
    # Load tables from file
    db_commutators = []
    csv_rw.member_access_read('access_tables.csv', db_commutators, [], [], [], [])

    commutators = []
    for commutator in db_commutators:
      # Find section in config file
      print commutator
      if config.has_section(commutator):
          commutators.append(commutator)
      
    return commutators

def send_commutator_command(commutator_name, command_name):    
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
            #print('Creating a link to %s (id = %d) on channel %d.' % (commutator, commutator_id, channel))
            link = LinkCommand(radio, channel,
                               commutator_id, commutator)
            status = {"commutator_ok": True}
            if command_name == 'check':
                status = link.check()
                if status["commutator_ok"]:
                    print('Commutator %s is functional.' % commutator)
                    logging.info('Commutator %s is functional.' % commutator)
                else:
                    print('Commutator %s did not answer as expected (%s)' % (commutator, status))
            elif command_name == 'auto':
                status = link.auto()
                if status["commutator_ok"]:
                    print('Commutator %s set to automatic mode.' % commutator)
                    logging.info('Commutator %s set to automatic mode.' % commutator)
                else:
                    print('Commutator %s did not answer as expected (%s)' % (commutator, status))
            elif command_name == 'on':
                status = link.enable_commutator()
                if status["commutator_ok"]:
                    print('Commutator %s set to always on mode.' % commutator)
                    logging.info('Commutator %s set to always on mode.' % commutator)
                else:
                    print('Commutator %s did not answer as expected (%s)' % (commutator, status))
            elif command_name == 'off':
                status = link.disable_commutator()
                if status["commutator_ok"]:
                    print('Commutator %s set to always off mode.' % commutator)
                    logging.info('Commutator %s set to always off mode.' % commutator)
                else:
                    print('Commutator %s did not answer as expected (%s)' % (commutator, status))
            elif command_name == 'clear_memory':
                status = link.clear_memory()
                if status["commutator_ok"]:
                    print('Commutator %s memory was cleared.' % commutator)
                    logging.info('Commutator %s memory was cleared.' % commutator)
                else:
                    print('Commutator %s did not answer as expected (%s)' % (commutator, status))
            elif command_name == 'single_activation':
                status = link.single_activation()
                if status["commutator_ok"]:
                    print('Commutator %s set to single activation mode.' % commutator)
                    logging.info('Commutator %s set to single activation mode.' % commutator)
                else:
                    print('Commutator %s did not answer as expected (%s)' % (commutator, status))
            elif command_name == 'double_activation':
                status = link.double_activation()
                if status["commutator_ok"]:
                    print('Commutator %s set to double activation mode.' % commutator)
                    logging.info('Commutator %s set to double activation mode.' % commutator)
                else:
                    print('Commutator %s did not answer as expected (%s)' % (commutator, status))
            elif command_name == 'check_memory':
                status = link.check_memory()
                if status["commutator_ok"]:
                    print("Memory state on %s: %d/%d used." % (commutator, status["mem_used"], status["mem_size"]))
                    # -> Logging entry set by function call
                else:
                    print('Commutator %s did not answer as expected (%s)' % (commutator, status))
            #obs = radio.read_register(NRF24.OBSERVE_TX)
            #radio.print_observe_tx(obs)


    
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
        
    parser_sdr = subparsers.add_parser('commutator_check_memory', description='Checks commutator memory.')
    parser_sdr.add_argument('-n', '--commutator_name', default='all', help=commutator_name_help)
    parser_sdr.set_defaults(func=commutator_check_memory)
        
    parser_sdr = subparsers.add_parser('commutator_clear_memory', description='Clears commutator memory.')
    parser_sdr.add_argument('-n', '--commutator_name', default='all', help=commutator_name_help)
    parser_sdr.set_defaults(func=commutator_clear_memory)
        
    parser_sdr = subparsers.add_parser('commutator_single_activation', description='Sets commutator single activation mode.')
    parser_sdr.add_argument('-n', '--commutator_name', default='all', help=commutator_name_help)
    parser_sdr.set_defaults(func=commutator_single_activation)
        
    parser_sdr = subparsers.add_parser('commutator_double_activation', description='Sets commutator double activation mode.')
    parser_sdr.add_argument('-n', '--commutator_name', default='all', help=commutator_name_help)
    parser_sdr.set_defaults(func=commutator_double_activation)
        
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
        os.chmod(log_file[0], 0o777)
    # Execute required function 
    args.func(args)

        
        
