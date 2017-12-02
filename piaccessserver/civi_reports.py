# -*- coding: utf-8 -*-

import sys

import ConfigParser
# Can be installed on Windows using py -2.7 -m pip install xlsxwriter
import xlsxwriter
import logging
import csv
import string
import MySQLdb
import kitchen
    
def read_db(events, config_filename):
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
                         use_unicode=True) 

    cur = db.cursor()

    # RAPPORT 1 : 
    # Nom du participant  `civicrm_participant`.`event_id` + contact_id
    # Courriel `civicrm_email.email` (key -> contact_id) is_primary = 1
    # Événement `civicrm_event.id` `civicrm_event.title` start_date >= CURDATE()
    # Statut -> `civicrm_participant.status_id` Est l'un de Enregistré, Présent, Pending (pay later), Partially paid
    #           `civicrm_participant_status_type.id` check against 'label'
    # Rôle -> Est l'un de Participant formation, Bénévole
    # Date d'enregistrement
    # Date de début de l'événement
    # Statut de la contribution

    get_event_req =  """SELECT DISTINCT 
                          `civicrm_contact`.`display_name`,
                          `civicrm_email`.`email`,
                          `civicrm_event`.`title`,
                          `civicrm_participant_status_type`.`label`,
                          `civicrm_participant`.`register_date`,
                          `civicrm_event`.`start_date`,
                          `civicrm_option_value`.`label`
                          
                        FROM 
                          `sherbro3_civicrm`.`civicrm_contact`,
                          `sherbro3_civicrm`.`civicrm_participant`,
                          `sherbro3_civicrm`.`civicrm_participant_status_type`,
                          `sherbro3_civicrm`.`civicrm_event`,
                          `sherbro3_civicrm`.`civicrm_email`, 
                          `sherbro3_civicrm`.`civicrm_option_value`, 
                          `sherbro3_civicrm`.`civicrm_option_group` 
               
                        WHERE `civicrm_participant`.`contact_id` = `civicrm_contact`.`id`
                          AND `civicrm_option_value`.`option_group_id` = 13
                          AND `civicrm_participant`.`role_id` = `civicrm_option_value`.`value`
                          AND `civicrm_email`.`contact_id` = `civicrm_contact`.`id`
                          AND `civicrm_participant`.`status_id` = `civicrm_participant_status_type`.`id`
                          AND `civicrm_email`.`is_primary` = 1
                          AND `civicrm_event`.`id` = `civicrm_participant`.`event_id`
                          AND `civicrm_event`.`start_date` >= CURDATE()
                          AND `civicrm_participant`.`status_id` IN (1,2,5,14)
                          AND `civicrm_participant`.`role_id` IN (1,2)
                        
                        ORDER BY `civicrm_event`.`title` ASC
                        ;"""

    try:
        cur.execute(get_event_req)
        event_req = cur.fetchall()

        logging.info("All data retrieved from database.")

        events.extend(event_req)
        return True
        
    except MySQLdb.Error as e:
        logging.error("Impossible to retrieve data: error received: %s" % e)
        return False
        
    finally:            
        if db:    
            db.close()


def write_report(filename, events):

    # Build csv file header with column names
    csv_header = (u"Nom du participant",
                  u"Courriel",
                  u"Évènement",
                  u"Statut",
                  u"Rôle",
                  u"Date d''enregistrement",
                  u"Date de début de l''évènement",
                  u"Statut de la contribution")

    # Write CSV file with returned results
    with open(filename, 'wb') as csvfile:
        infowriter = csv.writer(csvfile, delimiter=';')
        csv_header = [kitchen.text.converters.to_utf8(s) for s in csv_header]
        infowriter.writerow(csv_header)
        for event in events: 
            event = [s.encode('utf-8') for s in event]
            infowriter.writerow(event)

def write_excel(filename, events):

    # Build csv file header with column names
    header = (u"Nom du participant",
                  u"Courriel",
                  u"Évènement",
                  u"Statut",
                  u"Rôle",
                  u"Date d''enregistrement",
                  u"Date de début de l''évènement",
                  u"Statut de la contribution")
    
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet('Formations')
    worksheet.write_row(0, 0, header)
    
    # Start from the second row. Rows and columns are zero indexed.
    row = 1

    # Iterate over the data and write it out row by row.
    for event in events:
        for event_str in event:
            if isinstance(event_str, str):
                # Convert to unicode
                event_str = kitchen.text.converters.to_utf8(event_str)

        worksheet.write_row(row, 0, event)
        row += 1

    workbook.close()    
    

# UNIT TEST (if script is executed directly)
if __name__ == '__main__':

    if False:
        events = []
        
        # Test db data retrieval
        config_filename = 'db_connect_fields.ignored'
        read_db(events, config_filename)

        # Inspect outputs
        print(events) 
    else:
        # Provide dummy data to function
        events = ((u'Chamberland1, Lysane', u'lysane.chamberland@icloud.com', u'La planche à découper de vos rêves!', u'Enregistré', u'Participant formation', u'31 octobre 2017 2:08 PM', u'1 novembre 2017 5:30 PM', u'Completed'),
                  ('Chamberland2, Lysane', 'chamberland@icloud.com', 'La planche', u'Enregistré', 'Participant formation', '31 octobre 2018 2:08 AM', '34 novembre 2017 5:30 PM', 'Completed'),
                  ('Chamberland3, Lysane', 'lysane@icloud.com', u'vos rêves!', u'Enregistré', u'Bénévole', '31 octobre 2017 2:08 PM', '1 novembre 2017 5:30 PM', 'Pending'),
                  )
  
    from os import remove
    csv_filename = 'test_civi_reports.csv'

    # Remove previous csv test file
    try:
        remove(csv_filename)
    except:
        pass

    # Write data to file
    write_report(csv_filename,
                 events)
    
    xlsx_filename = 'test_civi_reports.xlsx'

    # Remove previous excel test file
    try:
        remove(xlsx_filename)
    except:
        pass

    # Write data to file
    write_excel(xlsx_filename,
                events)
    


