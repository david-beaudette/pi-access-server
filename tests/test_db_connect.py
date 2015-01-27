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

# Find the tags related to access parameters (machine names)
get_machine_req = """SELECT  `civicrm_tag`.`id`,
                           `civicrm_tag`.`name`
                   FROM    `sherbro3_civicrm`.`civicrm_tag`
                   WHERE   `civicrm_tag`.`parent_id` =
                   (SELECT  `civicrm_tag`.`id`
                   FROM    `sherbro3_civicrm`.`civicrm_tag`
                   WHERE   `civicrm_tag`.`name` = 'Accès');"""

# Find the card numbers and associated member id's
get_card_req = """SELECT `civicrm_value_carte_d_acc_s_4`.`entity_id`,
                         `civicrm_value_carte_d_acc_s_4`.`num_ro_22`,
                         `civicrm_value_carte_d_acc_s_4`.`code_hexad_cimal_23`
                    FROM `sherbro3_civicrm`.`civicrm_value_carte_d_acc_s_4`;"""

# Find the contacts that have a card assigned
get_member_req = """SELECT `civicrm_contact`.`display_name`,
                           `civicrm_contact`.`id` 
                    FROM `sherbro3_civicrm`.`civicrm_contact` 
                    WHERE `civicrm_contact`.`id` IN 
                    (SELECT `civicrm_value_carte_d_acc_s_4`.`entity_id` 
                    FROM `sherbro3_civicrm`.`civicrm_value_carte_d_acc_s_4`);"""

# Find the tags associated with members with cards
get_tag_req = """SELECT `civicrm_entity_tag`.`entity_id`,
                        `civicrm_entity_tag`.`tag_id`
                 FROM `sherbro3_civicrm`.`civicrm_entity_tag`
                 WHERE `civicrm_entity_tag`.`tag_id` IN
                 (SELECT  `civicrm_tag`.`id`
                  FROM    `sherbro3_civicrm`.`civicrm_tag`
                  WHERE   `civicrm_tag`.`parent_id` =
                  (SELECT  `civicrm_tag`.`id`
                   FROM    `sherbro3_civicrm`.`civicrm_tag`
                   WHERE   `civicrm_tag`.`name` = 'Accès'));"""

try:
    cur.execute(get_machine_req)
    machine_req = cur.fetchall()
    print(machine_req)
    
    cur.execute(get_card_req)
    card_req = cur.fetchall()
    print(card_req)
    
    cur.execute(get_member_req)
    member_req = cur.fetchall()
    print(member_req)
    
    cur.execute(get_tag_req)
    tag_req = cur.fetchall()
    print(tag_req)

    print("All data retrieved from database.")
    b_load_file = False
    
except MySQLdb.Error as e:
    print("An error has been passed. %s" % e)
    print("Will load values from csv file if found.")
    # Real code should do that...
    b_load_file = True
    
finally:            
    if db:    
        db.close()

# Build csv file header with column names
csv_header = ['Id du membre', 'Nom du membre',
              'Numéro de carte', 'Code de la carte']
# Add machine names
for machine in machine_req:
    csv_header.append(machine[1])

# Write CSV file with returned results
with open('ContactInfo.csv', 'w', newline='') as csvfile:
    infowriter = csv.writer(csvfile, delimiter=';')
    infowriter.writerow(csv_header)
    for member in member_req:
        # Id and name
        csv_member = [member[1], member[0]]
        # Card number and code
        for card in card_req:
            if card[0] == member[1]:
                #print("Le membre: %s a la carte #: %s" % (member[0], card[1]))
                csv_member.append(card[1])
                csv_member.append(card[2])
        # Access to each machine
        member_machines = []
        for tag in tag_req:
            if tag[0] == member[1]:
                member_machines.append(tag[1])
        #print("Le membre %s, machines #: %s" % (member[0], str(member_machines)))
        for i in range(len(machine_req)):
            b_machine_found = False
            for m in member_machines:
                if m == machine_req[i][0]:
                    #print("Le membre %s a accès à %s" % (member[0], machine_req[i][1]))
                    b_machine_found = True
            if b_machine_found:
                csv_member.append('1')
            else:
                csv_member.append('0')
                    
            
                    
        infowriter.writerow(csv_member)
        
