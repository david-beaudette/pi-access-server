import configparser
import csv
import string
import MySQLdb

# Read parameter file
config = configparser.ConfigParser()
config.read('test_db_connect.ini')
civi_host = config['DATABASE']['civi_host']
civi_db   = config['DATABASE']['civi_db']
civi_user = config['DATABASE']['civi_user']
civi_pw   = config['DATABASE']['civi_pw']

# Connect to CiviCRM database to retrieve contact parameters
db = MySQLdb.connect(host=civi_host, # your host, usually localhost
                     user=civi_user, # your username
                     passwd=civi_pw, # your password
                     db=civi_db) # name of the data base

cur = db.cursor()

# Find the parent ID of tags related to access parameters
get_parent_req = """SELECT  `civicrm_tag`.`id`
                    FROM    `sherbro3_civicrm`.`civicrm_tag`
                    WHERE   `civicrm_tag`.`name` = 'Accès';"""


try:
    cur.execute(get_parent_req)
    parent_req = cur.fetchall()
    print(parent_req)
    tag_parent_id = parent_req[0][0]
    print(tag_parent_id)

    get_child_req = """SELECT  `civicrm_tag`.`name`
                       FROM    `sherbro3_civicrm`.`civicrm_tag`
                       WHERE   `civicrm_tag`.`parent_id` = """ + str(tag_parent_id) + ";"""

    print(get_child_req)
    cur.execute(get_child_req)
    child_req = cur.fetchall()
    print(child_req)
    
except MySQLdb.Error as e:
    print("An error has been passed. %s" % e)
    
finally:            
    if db:    
        db.close()

# Write CSV file with returned results
#with open('ContactInfo.csv', 'w', newline='') as csvfile:
#    infowriter = csv.writer(csvfile, delimiter=';')
#    infowriter.writerow(['Spam'] * 5 + ['Baked Beans'])
#    infowriter.writerow(['Spam', 'Lovely Spam', 'Wonderful Spam'])

