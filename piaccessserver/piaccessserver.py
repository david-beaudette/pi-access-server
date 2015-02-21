import sys
import ConfigParser
import time

import db_connect
import link_command
import csv_rw


def piaccessserver_init():
    # Initialise radio

    # Initialise log file
    pass


def piaccessserver_loop(config_filename):
    # Initialise output arguments
    machines = []
    members = []
    cards = []
    tags = []
    
    # Read data from database
    db_connect.read_db(machines, members, cards, tags, config_filename)

        # If successful, write result in csv file


        # If not, read from csv file


    # Update access entries for all machines

        # Send command

        # If there are any updates, write them to local log
        

    # Retrieve log entries from all machines

        # Send command

        # If there are any entries, write them to local log

    
    # Check memory usage on all machine

        # Send command

        # If memory exceeds threshold, write warning to local log


if __name__ == '__main__':
    # Check if a config filename was provided
    if len(sys.argv) > 1:
        config_filename = sys.argv[1]
    else:
        config_filename = 'piaccessserver.ini'

    # Initialise server
    config = ConfigParser.RawConfigParser()
    piaccessserver_init()

    # Process server tasks
    while True:
        # Refresh server configuration
        config.read(config_filename)

        # Process tasks
        piaccessserver_loop(config_filename)

        # Wait for next loop iteration
        time.sleep(config.getfloat('ACCESS_SERVER', 'loop_delay'))
         

        
        
