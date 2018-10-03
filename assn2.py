import argparse
import openstack
import errno
import os

IMAGE = 'ubuntu-16.04-x86_64'
FLAVOUR = 'c1.c1r1'
NETWORK = 'assn2-net'
KEYPAIR = 'warnaa1-assn2-Key'
PRIVATE_KEYPAIR_FILE = './assn2/warnaa1-assn2-Key'
SERVER = 'warnaa1-assn2-server'

# create openstack connection using credentials from clouds.yml
conn = openstack.connect(cloud_name='op_cloud') 

#####################FUNCTIONS####################################

# Check for assn-2 network
def check_network(conn):
    networkcheck = conn.network.find_network(NETWORK)
    if networkcheck is None:
        print("Network 'assn2-net' not found!:")
        print("Exiting...:")
        exit(1)
    else: 
        print("Network assn2-net found")

#Create Keypair
def create_keypair(conn):
    print("\nChecking for Key pair....")
    keypair = conn.compute.find_keypair(KEYPAIR)
    SSH_DIR = './assn2'
    if not keypair:
        print("\nNo Key Pair found...")
        print("Create Key Pair:")

        keypair = conn.compute.create_keypair(name=KEYPAIR)

        print(keypair)

        try:
            os.mkdir(SSH_DIR)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e

        with open(PRIVATE_KEYPAIR_FILE, 'w') as f:
            f.write("%s" % keypair.private_key)

        os.chmod(PRIVATE_KEYPAIR_FILE, 0o777)
        print("\nKey Pair Created Successfully!")

    else:
        print("\nKey Pair found")

    return keypair

#Create an Instance(Server)
def create_server(conn):

    print("\nCreate Server:")
    print("...................................")
    print("\nChecking if Server Already Exist....")
    try:
        server = conn.compute.find_server(SERVER)
        print("\nServer Found: "+str(server))
        if server is None:
             print("\nCreating Server: "+SERVER)
             image = conn.compute.find_image(IMAGE)
             flavour = conn.compute.find_flavor(FLAVOUR)
             network = conn.network.find_network(NETWORK)
             keypair = create_keypair(conn)

             server = conn.compute.create_server(
                 name=SERVER, image_id=image.id, flavor_id=flavour.id,
                 networks=[{"uuid": network.id}], key_name=keypair.name)

             server = conn.compute.wait_for_server(server)
             print('\nServer Created: '+SERVER)
        else:
            print("\nServer Found, Can not Create the same server")
            exit(1)
    except Exception as e:
         print(e)
         print("The server created error")


#Create Floating IP's
def create_floating_ip(conn):
    print("\nCreating floating ip:")
    print("...................................")
    print("\nObtaining Server and Network")
    public_net = conn.network.find_network('public-net')
    server = conn.compute.find_server(SERVER)    
    print("\nChecking if public net is available :")
    print("......................................")
    #Check if public net is available, and create if not
    if public_net is not None:
        floating_ip = conn.network.create_ip(floating_network_id=public_net.id)
        conn.compute.add_floating_ip_to_server(server, floating_ip.floating_ip_address)
        print("\nFloating ip created and Assigned to the Server "+SERVER)
        print("...................................")

#Display report information for all servers in group
def display_report(conn):
    print("\nPrinting Report:")
    print("************************")
    for svr in conn.compute.servers():
            print("\nPrinting Server Name:")
            print("............................")
            print(svr.name)
            print("\nPrinting Server Status:")
            print("............................")
            print(svr.status)
            print("\nPrinting Image Name")
            print("............................")
            imgID = svr.image['id']
            img = conn.compute.find_image(imgID)
            print(img.name)
            print('\nPrinting IP Information:')
            print("............................")
            for net in svr.addresses.values():
                for address in net:
                        print(address['addr'])
            
            print("\n")
    

#Delete A Server
def delete_server(conn):

    print("\nServer Deletion:") 
    print("...................................")
    print("Finding Server....")
    try:
        server = conn.compute.find_server(SERVER)
        print("Server Found: "+str(server))
        if server is not None:
             print("Deleting Server: "+SERVER)
             server = conn.compute.delete_server(server, ignore_missing=True, force=False)
             print('Server Removed')
        else:
            print("No Server Found, Can not Delete Server")
    except Exception as e:
         print(e)
         print("The server has been removed already")


#Deleting the floating IP
def delete_floatingIP(conn):

     required = 'floating'
     for svr in conn.compute.servers(name=SERVER):
            print('\nGetting Floating IP Information:')
            print("...................................")
            for net in svr.addresses.values():
                print('\nPrinting Floating IP.....')
                for address in net:
                    if required in address['OS-EXT-IPS:type']:
                        print(address['OS-EXT-IPS:type'])
                        print(address['addr'])
                        floatIP = address['addr']
    
     print("Finding Server To Remove Floating IP")
     print("....................................")
     try:
         server = conn.compute.find_server(SERVER)
         print("Server Found: "+str(server))
         if server is not None:
             print("Deleting Floating Ip")
             conn.compute.remove_floating_ip_from_server(server,floatIP)
             print('Floating IP Removed')
         else:
             print("No Server, No Floating IP to remove")
     except Exception as e:
         print(e)
         print("Either the server or the Floating IP has been removed already")


def delete_keypair(conn):
    print("\nGetting Key Pair")
    print("...................................")
    keypair = conn.compute.find_keypair(KEYPAIR)
    if keypair is not None:
            print('Key Pair found, Deleting')
            conn.compute.delete_keypair(keypair, ignore_missing=True)
            print("Key Pair Deleted...")
    else:
         print('No Key Pair found, No Key pair to remove')
    

#Display the report for when instance has been created  
def display_report_no2(conn):
        print('Reporting For Server:')
        required = 'floating'
        for svr in conn.compute.servers(name=SERVER):
            print("Instance Name: "+svr.name)
            for net in svr.addresses.values():
                #print(net)
                #print('\nPrinting Floating IP.....')
                for address in net:
                    if required in address['OS-EXT-IPS:type']:
                        print("Floating IP: "+address['addr'])


        keypair = conn.compute.find_keypair(KEYPAIR)
        print("Private Key: "+str(keypair))


# get command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('operation', help='One of "report",  "up" or "down"')
args = parser.parse_args()

if args.operation == 'report':
       try:
           display_report(conn)
       except Exception as e:
           print("Report Error")
           print(e)
      # print a report on instances
       pass
elif args.operation == 'up':
        try:
            check_network(conn)         
            create_keypair(conn)
            create_server(conn)
            create_floating_ip(conn)
            display_report_no2(conn)
        except Exception as e:
                print("There was a problem with create functions")
                print (e)
       
        pass
    # bring up various openstack resources
elif args.operation == 'down':
    # tear down openstack resources if they are present
        try:
            delete_floatingIP(conn)
            delete_server(conn)
            delete_keypair(conn)
        except Exception as e:
                print("There was a problem with Delete functions")
                print(e)
       
        pass
