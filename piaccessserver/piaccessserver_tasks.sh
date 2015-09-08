#!/bin/bash
cd /home/pi/git/pi-access-server/piaccessserver
sudo python piaccessserver.py commutator_get_log
sudo python piaccessserver.py server_db_retrieve
sudo python piaccessserver.py commutator_update
