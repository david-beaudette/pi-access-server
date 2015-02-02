# coding: utf-8
import ConfigParser
import csv
import string
import MySQLdb

def read_db(machines, members, cards, tags):
    # Read parameter file
    config = ConfigParser.RawConfigParser()
    config.read('db_connect.ini')
    civi_host = config.get('DATABASE', 'civi_host')
    civi_db   = config.get('DATABASE', 'civi_db')
    civi_user = config.get('DATABASE', 'civi_user')
    civi_pw   = config.get('DATABASE', 'civi_pw')

    # Connect to CiviCRM database to retrieve contact parameters
    db = MySQLdb.connect(host=civi_host, # your host, usually localhost
                         user=civi_user, # your username
                         passwd=civi_pw, # your password
                         db=civi_db,     # name of the data base
                         charset='utf8',
                         use_unicode=False) 

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
        #print(machine_req)
        
        cur.execute(get_card_req)
        card_req = cur.fetchall()
        #print(card_req)
        
        cur.execute(get_member_req)
        member_req = cur.fetchall()
        #print(member_req)
        
        cur.execute(get_tag_req)
        tag_req = cur.fetchall()
        #print(tag_req)

        print("db_connect-read_db: All data retrieved from database.")

        machines.extend(machine_req)
        cards.extend(card_req)
        members.extend(member_req)
        tags.extend(tag_req)
        return True
        
    except MySQLdb.Error as e:
        print("An error has been passed. %s" % e)
        print("Will load values from csv file if found.")
        # Real code should do that...
        return False
        
    finally:            
        if db:    
            db.close()



# UNIT TEST (if script is executed directly)
if __name__ == '__main__':
    import access_mgt
    machines = []
    members = []
    cards = []
    tags = []
    
    # Test db data retrieval
    read_db(machines, members, cards, tags)

    # Inspect outputs
    print(machines) 
    print(members) 
    print(cards) 
    print(tags) 


