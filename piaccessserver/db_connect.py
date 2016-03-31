# coding: utf-8
import ConfigParser
import logging
import csv
import string
import MySQLdb

def read_db(commutators, members, memberships, cards, tags, config_filename):
    # Read parameter file
    config = ConfigParser.RawConfigParser()
    config.read(config_filename)
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

    # Find the tags related to access parameters (commutator names)
    get_commutator_req = """SELECT  `civicrm_tag`.`id`,
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

    # Find the contacts that have a valid membership
    get_membership_req = """SELECT `civicrm_contact`.`display_name`,
                               `civicrm_contact`.`id` 
                            FROM `sherbro3_civicrm`.`civicrm_contact` 
                            WHERE `civicrm_contact`.`id` IN 
                            (SELECT `civicrm_membership`.`contact_id` 
                            FROM `sherbro3_civicrm`.`civicrm_membership` 
                            WHERE `civicrm_membership`.`membership_type_id` 
                            IN (11,12,13,16,17,18,19,20,21,22,23) AND `civicrm_membership`.`end_date` >= CURDATE());"""

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
        cur.execute(get_commutator_req)
        commutator_req = cur.fetchall()
        #print(commutator_req)
        
        cur.execute(get_card_req)
        card_req = cur.fetchall()
        #print(card_req)
        
        cur.execute(get_member_req)
        member_req = cur.fetchall()
        #print(member_req)
        
        cur.execute(get_membership_req)
        membership_req = cur.fetchall()
        #print(membership_req)
        
        cur.execute(get_tag_req)
        tag_req = cur.fetchall()
        #print(tag_req)

        logging.info("All data retrieved from database.")

        commutators.extend(commutator_req)
        cards.extend(card_req)
        members.extend(member_req)
        memberships.extend(membership_req)
        tags.extend(tag_req)
        return True
        
    except MySQLdb.Error as e:
        logging.error("Impossible to retrieve data: error received: %s" % e)
        return False
        
    finally:            
        if db:    
            db.close()



# UNIT TEST (if script is executed directly)
if __name__ == '__main__':
    commutators = []
    members = []
    memberships = []
    cards = []
    tags = []
    
    # Test db data retrieval
    config_filename = 'db_connect_fields.ignored'
    read_db(commutators, members, memberships, cards, tags, config_filename)

    # Inspect outputs
    print(commutators) 
    print(members) 
    print(memberships) 
    print(cards) 
    print(tags) 


