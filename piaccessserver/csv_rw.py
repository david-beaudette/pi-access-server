# coding: utf-8
import string
import csv

def member_access_write(filename,
                        machine_req,
                        member_req,
                        membership_req,
                        card_req,
                        tag_req):
    # Build csv file header with column names
    csv_header = ['Id du membre', 
                  'Nom du membre',
                  'Numéro de carte', 
                  'Code de la carte',
                  'Adhésion valide']
    # Add machine names
    for machine in machine_req:
        csv_header.append(machine[1])

    # Write CSV file with returned results
    with open(filename, 'wb') as csvfile:
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
            # Membership validity     
            b_membership_valid = False
            for membership in membership_req:
                if membership[1] == member[1]:
                    b_membership_valid = True
            if b_membership_valid:
                csv_member.append('1')
            else:
                csv_member.append('0')
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



def member_access_read(filename,
                       machines,
                       members,
                       memberships,
                       cards,
                       autorisations):
                                
    # Read back CSV file and load information for each machine
    # Returned tuple 
    with open(filename, 'r') as csvfile:
        inforeader = csv.reader(csvfile, delimiter=';')
        header_row = inforeader.next()
        machine_list = header_row[5:]
        for machine in machine_list:
            # Add the machine name
            machines.append(machine)
            # Add an empty autorisation list
            autorisations.append([])
        for member in inforeader:
            #print member[1]
            # Check if member has a valid card number
            if len(member[3]) == 8 and \
               all(c in string.hexdigits for c in member[3]):
                cards.append(member[3])
                members.append(member[1])
                if int(member[4]):
                    # Access granted
                    memberships.append(True)
                else:
                    # Access refused
                    memberships.append(False)
                # Check if the member has access to each machine 
                for machine_num in range(len(machine_list)):
                    if int(member[5 + machine_num]):
                        # Access granted
                        autorisations[machine_num].append(True)
                    else:
                        # Access refused
                        autorisations[machine_num].append(False)
                    

                
    return True

# UNIT TEST (if script is executed directly)
if __name__ == '__main__':
    from os import remove
    csv_filename = 'test_csv_rw.csv'

    # Remove previous test file
    try:
        remove(csv_filename)
    except:
        pass

    # Provide dummy data to function
    machines = ((7L, 'Degauchisseuse'),
                (8L, 'Tour - Fraiseuse'),
                (10L, 'Planeur'))
    members = (('Francis Poisson-Gagnon', 2L),
                ('David Beaudette', 3L),
                ('David Moreau Bastien', 4L),
                ('Gabriel Rebêlo', 5L))
    memberships = (('Francis Poisson-Gagnon', 2L),
                ('David Beaudette', 3L),
                ('Nobody Gauthier', 22L),
                ('Ibrahim Ferrer', 678L))
    cards = ((3L, 'F1', '7040840B'),
             (4L, 'F2', '5084F754'),
             (2L, 'F3', '03871AC1'),
             (5L, 'FX', '45555555'))
    
    # This means tag_req[i][0] member has access to tag_req[i][1] machine
    tags = ((3L, 7L),
            (5L, 7L),
            (2L, 10L),
            (5L, 8L))

    # Write data to file
    member_access_write(csv_filename,
                        machines,
                        members,
                        memberships,
                        cards,
                        tags)
    
    # Retrieve from same file
    machines_r = []
    cards_r = []
    members_r = []
    memberships_r = []
    authorisations_r = []
    member_access_read(csv_filename,
                       machines_r,
                       members_r,
                       memberships_r,
                       cards_r,
                       authorisations_r)

    # Inspect output
    print(machines_r)
    print(members_r)
    print(memberships_r)
    print(cards_r)
    print(authorisations_r)
    
    for i in range(len(authorisations_r)):
        for j in range(len(authorisations_r[i])):
            authorisations_r[i][j] = authorisations_r[i][j] and memberships_r[j]
            
    print(authorisations_r)
           