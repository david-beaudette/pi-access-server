
import string
import csv


def member_access_write(machine_req, member_req, card_req, tag_req):
    # Build csv file header with column names
    csv_header = ['Id du membre', 'Nom du membre',
                  'Numéro de carte', 'Code de la carte']
    # Add machine names
    for machine in machine_req:
        csv_header.append(machine[1])

    # Write CSV file with returned results
    with open('ContactInfo.csv', 'w') as csvfile:
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



def member_access_read():
                                
    # Read back CSV file and load information for each machine
    with open('ContactInfo.csv', 'r') as csvfile:
        inforeader = csv.reader(csvfile, delimiter=';')
        for machine_num in range(len(machine_req)):
            print machine_req[machine_num][1]
            for row in inforeader:
                # Check if the member has access to the machine
                if int(row[4+machine_num]):
                    print row
