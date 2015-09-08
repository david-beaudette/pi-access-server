#!/bin/bash
cd /home/pi/git/pi-access-server/piaccessserver
sudo python piaccessserver.py server_new_log
sudo python piaccessserver.py commutator_new_log
echo "New log created."
