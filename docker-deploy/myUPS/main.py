import socket
import threading
from concurrent.futures import ThreadPoolExecutor
import world_ups_pb2
import amazon_ups_pb2
import time
from db_handle import *
from google.protobuf.internal.encoder import _VarintBytes
from google.protobuf.internal.encoder import _VarintEncoder
from google.protobuf.internal.decoder import _DecodeVarint
import os

# for the docker
# AMAZON_HOST = os.getenv('AMAZON_HOST', 'vcm-38978.vm.duke.edu')
# AMAZON_PORT = int(os.getenv('AMAZON_PORT', 22222))
# WORLD_HOST = os.getenv('WORLD_HOST', 'vcm-38978.vm.duke.edu')
# WORLD_PORT = int(os.getenv('WORLD_PORT', 12345))
AMAZON_HOST = os.getenv('AMAZON_HOST')
AMAZON_PORT = int(os.getenv('AMAZON_PORT'))
WORLD_HOST = os.getenv('WORLD_HOST')
WORLD_PORT = int(os.getenv('WORLD_PORT'))

# kaixin
# AMAZON_HOST = "vcm-38044.vm.duke.edu" 
# AMAZON_PORT = 9008
# WORLD_HOST = "vcm-38044.vm.duke.edu"
# WORLD_PORT = 12345

# sitang
# AMAZON_HOST = "vcm-39217.vm.duke.edu" 
# AMAZON_PORT = 1357
# WORLD_HOST = "vcm-39217.vm.duke.edu"
# WORLD_PORT = 12345

# yijia
# AMAZON_HOST = "vcm-38978.vm.duke.edu" 
# AMAZON_PORT = 22222
# WORLD_HOST = "vcm-38978.vm.duke.edu"
# WORLD_PORT = 12345

# #django
# DJANGO_HOST= "vcm-38978.vm.duke.edu" 
# DJANGO_PORT= 33333


socket_lock = threading.Lock()
executor = ThreadPoolExecutor(max_workers=50)

current_seqnum = 0
send_amazon_seqnum = {}
send_world_seqnum = {}
send_amazon_ACK = [] #check which ack have sent, so we will not handle in databse again except resending ACK
send_world_ACK =[]

amazon_fd = None
world_fd = None

truck_num = 5  # define the truck numbers when first connect with world, for the second time connect the same world, set to 0
UPDATE_INTERVAL = 5
RESEND_MSG_INTERVAL = 5
# IF_QUERY = True
DISCONNECT = False 


#-------------------------------------build connect with django ---------------------------------------

# def recv_Django_msg(django_fd):
#     """
#     Function to receive messages from the Django server.
#     It tries to receive a message and decode it.
#     """
#     try:
#         message = django_fd.recv(1024).decode()  # Decoding the received byte string.
#         return message
#     except Exception as e:
#         print(f"Error receiving message: {e}")
#         return None

# def parse_Django_msg(message):
#     """
#     Placeholder function to parse received AtoUCommands messages.
#     You would implement your message handling logic here.
#     """
#     ship_id, dest_x, dest_y = message.split(',')
#     print(f"Received ship_id: {ship_id}, dest_x: {dest_x}, dest_y: {dest_y}")
#     handle_Django_msg(ship_id,dest_x, dest_y)
#     # Add logic to process these values as needed.

# def connect_django(host, port):
  
#     django_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     django_fd.connect((host, port))

#     while True:
#             msg = recv_Django_msg(django_fd)
#             if msg is None:  # when the connection is closed or there's an error
#                 break
#             executor.submit(parse_Django_msg, msg)
#     django_fd.close()
#     print("Connection closed.")


# ###?? if package not out for delivery, ???
# def handle_Django_msg(packageid, new_dest_x, new_dest_y):
#     status = db_getPackage_status(packageid)
#     if status != "out for delivery"

#--------------------------------------helper function-------------------------------------------
def get_seqnum():
    global current_seqnum
    with socket_lock:
        current_seqnum += 1
        return current_seqnum
    
def encode_varint(value):
    """ Encode an int as a protobuf varint """
    data = []
    _VarintEncoder()(data.append, value, False)
    return b''.join(data)

def decode_varint(data):
    """ Decode a protobuf varint to an int """
    return _DecodeVarint(data, 0)[0]

#--------------------------------------connect with amazon and world -----------------------------
def create_client_socket(host, port):
    """Creates and returns a socket connected to the given host and port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    return s

'''Once get worldid from amazon, 1. build socket and connect 2. send Uconnect message 3. recv UConnected message to check if success'''
def connectWorld(world_id):
    global world_fd
    world_fd = create_client_socket(WORLD_HOST, WORLD_PORT) 
    print(f"socket with world:{world_fd}\n")
    try:
        Uconnect_msg = create_Uconnect_msg(world_id, False, truck_num)
        serialized_msg = Uconnect_msg.SerializeToString() 
        len_prefix = _VarintBytes(len(serialized_msg))
        world_fd.sendall(len_prefix + serialized_msg)
        Uconnected_msg = recv_world_msg(world_fd, "UConnected")
        print("Before initializing trucks in the database.")
        db_init_truck(truck_num)
        print("after initializing trucks in the database.")
        return world_fd
    # finally:
    #     client_socket.close()  # Ensure the socket is closed
    except:
        print("Error: build_connect_world() failed")
        
def create_Uconnect_msg(worldid, is_amazon, trucks_num):
    Uconnect = world_ups_pb2.UConnect()
    if worldid is not None:
        Uconnect.worldid = worldid
    Uconnect.isAmazon = is_amazon
    for truckid in range(1, trucks_num+1):
        UInitTruck = Uconnect.trucks.add()
        UInitTruck.id = truckid
        UInitTruck.x = 0
        UInitTruck.y = 0
    print (f"Uconnect: {Uconnect}")
    return Uconnect

def create_Uconnect_msg2(worldid, is_amazon):
    Uconnect = world_ups_pb2.UConnect()
    if worldid is not None:
        Uconnect.worldid = worldid
    Uconnect.isAmazon = is_amazon
    print (f"Uconnect: {Uconnect}")
    return Uconnect


#---------------------------------handle thread for each socket--------------------------------------
#keep listening, to recv the message, and submit each received message to a worker thread for parsing
def listen_to_amazon(amazon_fd):
    while True:
        msg = recv_Amazon_msg(amazon_fd, "AtoUCommands")
        if msg is None:  # when the connection is closed or there's an error
            break  
        executor.submit(parse_AtoUCommands,msg) #TODO: check if send ACK
        
def listen_to_world(world_fd):
    while True:
        msg = recv_world_msg(world_fd, "UResponses")
        if msg is None:  
            break
        executor.submit(parse_UResponses,msg) 

#------------------------------------- recv message -------------------------------------------
def recv_world_msg(world_fd, msg_type):
    data = b''
    while True:
        try:
            data += world_fd.recv(1)
            size = decode_varint(data)
            break 
        except IndexError:
            pass
    # Receive the message data
    data = world_fd.recv(size)
    # Decode the message
    if msg_type== "UConnected":
        UConnected_msg = world_ups_pb2.UConnected()
        UConnected_msg.ParseFromString(data)
        print(f"\nUConnected_msg: \n{UConnected_msg}")
        return UConnected_msg
    elif msg_type== "UResponses":
        UResponses_msg = world_ups_pb2.UResponses()
        UResponses_msg.ParseFromString(data)
        print(f"\nUResponses_msg: \n{UResponses_msg}")
        return UResponses_msg


def recv_Amazon_msg(amazon_fd, msg_type):
    # Receive the size of the message data
    data = b''
    while True:
        try:
            data += amazon_fd.recv(1)
            size = decode_varint(data)
            break
        except IndexError:
            pass
    # Receive the message data
    data = amazon_fd.recv(size)
    # Decode the message
    if msg_type== "ConnectWorldId":
        ConnectWorldId_msg = amazon_ups_pb2.ConnectWorldId()
        ConnectWorldId_msg.ParseFromString(data)
        print("ConnectWorldId_msg:\n", ConnectWorldId_msg, "\n")
        world_id = ConnectWorldId_msg.world_id
        seq_num = ConnectWorldId_msg.seq_num
        print(f"Received World ID from amazon: {world_id}\n")
        world_fd = connectWorld(world_id)
        sendACK_amazon(seq_num)
        return ConnectWorldId_msg, world_fd
        # return ConnectWorldId_msg
    elif msg_type== "AtoUCommands":
        AtoUCommands_msg = amazon_ups_pb2.AtoUCommands()
        AtoUCommands_msg.ParseFromString(data)
        print(f"\nAtoUCommands_msg: \n{AtoUCommands_msg}")
        return AtoUCommands_msg


#--------------------------------- parse message ----------------------------------

#TODO: handle finished, error
def parse_UResponses(UResponses_msg):
    if UResponses_msg.completions:
        for UFinished_msg in UResponses_msg.completions:
            handle_UFinished(UFinished_msg) 
    if UResponses_msg.delivered:
        for UDeliveryMade_msg in UResponses_msg.delivered:
            handle_UDeliveryMade(UDeliveryMade_msg)
    if UResponses_msg.acks:
        for ack in UResponses_msg.acks:
            handle_ack_from_world(ack)
    if UResponses_msg.truckstatus:
        for UTruck_msg in UResponses_msg.truckstatus:
            handle_UTruck(UTruck_msg)
    if hasattr(UResponses_msg, 'finished') and UResponses_msg.finished:
        handle_finished()
    if UResponses_msg.error:
        for UErr_msg in UResponses_msg.error:
            handle_UErr_msg(UErr_msg)


#TODO: handle error
def parse_AtoUCommands(AtoUCommands_msg):
    if AtoUCommands_msg.truckReqs:
        for RequestTruck_msg in AtoUCommands_msg.truckReqs:
            handle_RequestTruck(RequestTruck_msg)
    if AtoUCommands_msg.delivReqs:
        for DeliverPackage_msg in AtoUCommands_msg.delivReqs:
            handle_DeliverPackage(DeliverPackage_msg)
    if AtoUCommands_msg.acks:
        for ack in AtoUCommands_msg.acks:
            handle_ack_from_amazon(ack)
    if AtoUCommands_msg.error:
        for Err_msg in AtoUCommands_msg.error:
            handle_Err_msg(Err_msg)


#---------------------------------handle Amazon message----------------------------------

'''for requestTruck 1. parse data send message to world to UGoPickup(truckid, whid, seqnum) 2. recv from world completions 3. send to amazon truckArrived 4. recv from amazon deliverPackage 5. send to world UDeliveryLocation(with packageid, x, y) 6. recv from world delivered 7 send to amazon U2ADelivered'''

#TODO: check select truck, 
#TODO: if modify status of truck, package
# 1. check if the seqnum is handled before through check if we have sent ACK, if handled before, then just resend the ack
# 2. find best truck, send UGoPickup to world, then recv from world (UFinished) handle by another thread)
def handle_RequestTruck(RequestTruck_msg):
    seq_num = RequestTruck_msg.seq_num
    if seq_num in send_amazon_ACK:  #only resend ack
        sendACK_amazon(seq_num)
        return
    else:
        #1. sendACK 
        sendACK_amazon(seq_num) 
        #2.handle_db (create a package object, warehouse(if not exist), products (if include)), package status: "created"
        whid = RequestTruck_msg.warehouse_id 
        warehouse_x = RequestTruck_msg.warehouse_x
        warehouse_y = RequestTruck_msg.warehouse_y
        dest_x = RequestTruck_msg.dest_x
        dest_y = RequestTruck_msg.dest_y
        packageid = RequestTruck_msg.ship_id
        assign_truck = db_find_truck_pickup(whid)
        # if RequestTruck_msg.ups_oder:
        user_id = None
        products = []
        if RequestTruck_msg.HasField('ups_order'):
            user_id = RequestTruck_msg.ups_order.UPSuserId
            for product in RequestTruck_msg.ups_order.product:
                products.append((product.productId, product.productDescription, product.productCount))
        db_RequestTruck(whid, warehouse_x, warehouse_y, assign_truck, packageid, dest_x, dest_y, user_id=user_id, products=products) 

        #3. tell world UGoPickup, 
        seq_num, msg = create_UGoPickup_msg(assign_truck, whid)  
        sendMsg(world_fd, seq_num, msg, send_world_seqnum)
        #4. modify package status: "truck en route to warehouse "
        
        db_modify_package_status(packageid, 'truck en route to warehouse')
        db_modify_truck_status(assign_truck, 'traveling')


def handle_DeliverPackage(DeliverPackage_msg):  # DeliverPackage(seq_num, ship_id)
    seq_num = DeliverPackage_msg.seq_num
    if seq_num in send_amazon_ACK:  #only resend ack
        sendACK_amazon(seq_num)
        return
    else:
        sendACK_amazon(seq_num)
        
        packageid = DeliverPackage_msg.ship_id
        truckid = db_getTruckid(packageid)

        db_modify_truck_status(truckid, 'arrive warehouse') 
        packages_info = db_getLocation(packageid)
        for packageid, dest_x, dest_y in packages_info:
            seq_num, msg= create_UGoDeliver_msg(truckid, packageid, dest_x, dest_y ) 
            # UGoDeliver(truckid, UDeliveryLocation (packageid,x,y), seqnum)
            sendMsg(world_fd, seq_num, msg, send_world_seqnum)

            db_modify_package_status(packageid, 'out for delivery')
            db_modify_truck_status(truckid,'delivering')

            # send the final dest to amazon
            seq_num2, msg2 = create_FinalDest_msg(packageid,dest_x,dest_y)
            sendMsg(amazon_fd, seq_num2, msg2, send_amazon_seqnum)
    
def handle_Err_msg(Err_msg):
    seq_num = Err_msg.seq_num
    if seq_num in send_amazon_ACK:  #only resend ack
        sendACK_amazon(seq_num)
        return
    else:
        sendACK_amazon(seq_num) 
        print("ERROR FROM AMAZON: ",Err_msg)


#---------------------------------handle World message----------------------------------
'''completions You will receive this notification when either 
(a) a truck reaches the warehouse you sent it to (with a pickup command) and is ready to load a package or 
(b) a truck has finished all of its deliveries (that you sent it to make with a deliveries command).'''

#TODO: 1. modify package "en route to warehouse" status in other place, 2. the handle (b) if status == idle
#TODO: if modify status to be " truck waiting for package ?"
def handle_UFinished(UFinished_msg): #UFinished(truckid, x, y, status, seqnum)
    seq_num = UFinished_msg.seqnum
    if seq_num in send_world_ACK:  #only resend ack
        sendACK_world(seq_num)
        return
    else:
        #TODO: if modify the whid of chunk where to modify 
        sendACK_world(seq_num)
        truckid = UFinished_msg.truckid
        x = UFinished_msg.x
        y = UFinished_msg.y
        status = UFinished_msg.status
        if "ARRIVE WAREHOUSE" in status: #(a)situation
            whid = db_convertWhid(x, y)
            print( f"truckid : {truckid}, x: {x}, y:{y}, whid: {whid}")
            db_UFinished(truckid, x, y, whid)  # modify truck status: "arrive warehouse"
            #2. db find package with status (truck en route to warehouse), truckid, whid
            packages_info = db_findPackage_waiting_truck(truckid, whid)
            #3. tell amazon TruckArrived,  recv DeliverPackage request from amazon (handle by other thread)
            #3. modify package status: "truck waiting for package"
            for packageid, truckid in packages_info:
                print (f"packageid,{packageid}")
                print (f"truckid,{truckid}")
                seq_num, UtoACommands_msg = create_TruckArrived_msg(packageid, truckid)
                sendMsg(amazon_fd, seq_num, UtoACommands_msg, send_amazon_seqnum) 
                db_modify_package_status(packageid, 'truck waiting for package')
                #TODO: if check recv ack then modify
                db_modify_truck_status(truckid, 'loading')
        #TODO: check if a truck finish all the deliverys and send completions the status is idle ?
        elif status == "IDLE":  #(b)situation
            db_UFinished_idle(truckid, x, y)
            return 
        

def handle_UDeliveryMade(UDeliveryMade_msg): #UDeliveryMade(truckid, packageid, seqnum)
    seq_num = UDeliveryMade_msg.seqnum
    if seq_num in send_world_ACK:  #only resend ack
        sendACK_world(seq_num)
        return
    else:
        sendACK_world(seq_num)
        packageid = UDeliveryMade_msg.packageid
        truckid = UDeliveryMade_msg.truckid
        db_UDeliveryMade(packageid) # modify package status: "delivered"
        # tell amazon U2ADelivered(seq_num, ship_id)
        print ("enter query msg once recv the deliver from world")
        query_msg(truckid)
        seq_num, UtoACommands_msg = create_U2ADelivered_msg(packageid)
        sendMsg(amazon_fd, seq_num, UtoACommands_msg, send_amazon_seqnum)



def handle_UErr_msg(UErr_msg):
    seq_num = UErr_msg.seqnum
    if seq_num in send_world_ACK:  #only resend ack
        sendACK_world(seq_num)
        return
    else:
        sendACK_world(seq_num) 
        print("ERROR FROM WORLD: ", UErr_msg)
        

def handle_finished():
    # Close sockets and shutdown thread pool as part of cleanup
    global amazon_fd, world_fd, executor
    if world_fd:
        try:
            world_fd.close()
            print("World socket closed.")
        except Exception as e:
            print(f"Error closing world socket: {e}")
        world_fd = None

    if amazon_fd:
        try:
            amazon_fd.close()
            print("Amazon socket closed.")
        except Exception as e:
            print(f"Error closing Amazon socket: {e}")
        amazon_fd = None

    if executor:
        executor.shutdown(wait=True)
        print("Thread pool has been shut down.")
        executor = None 

#-----------------------------create message to world--------------------------------------------

def create_UGoPickup_msg(truckid, whid):
    UCommands = world_ups_pb2.UCommands()
    UCommands.disconnect = False
    UGoPickup= UCommands.pickups.add()  # Add a new UGoPickup
    UGoPickup.truckid = truckid
    UGoPickup.whid = whid
    seq_num = get_seqnum()
    UGoPickup.seqnum =  seq_num
    print(f"UCommands: {UCommands}")
    return seq_num, UCommands


def create_UGoDeliver_msg(truckid, packageid, dest_x, dest_y):
    UCommands = world_ups_pb2.UCommands()
    UCommands.disconnect = False
    UGoDeliver= UCommands.deliveries.add()  # Add a new UGoDeliver
    UGoDeliver.truckid = truckid
    seq_num = get_seqnum()
    UGoDeliver.seqnum =  seq_num
    UDeliveryLocation = UGoDeliver.packages.add() 
    UDeliveryLocation.packageid = packageid
    UDeliveryLocation.x = dest_x
    UDeliveryLocation.y = dest_y
    print(f"\nUCommands: \n{UCommands}")
    return seq_num, UCommands

#-----------------------------create message to amazon -------------------------------------------

def create_TruckArrived_msg(ship_id, truck_id):
    UtoACommands = amazon_ups_pb2.UtoACommands()
    TruckArrived = UtoACommands.arrived.add()
    seq_num = get_seqnum()
    TruckArrived.seq_num = seq_num
    TruckArrived.ship_id = ship_id
    TruckArrived.truck_id = truck_id
    print("\nUtoACommands: \n", UtoACommands)
    return seq_num, UtoACommands

  
def create_U2ADelivered_msg(ship_id):
    UtoACommands = amazon_ups_pb2.UtoACommands()
    U2ADelivered = UtoACommands.delivered.add()
    seq_num = get_seqnum()
    U2ADelivered.seq_num = seq_num
    U2ADelivered.ship_id = ship_id
    print("\nUtoACommands: \n", UtoACommands)
    return seq_num, UtoACommands

def create_FinalDest_msg(ship_id, final_dest_x, final_dest_y):
    UtoACommands = amazon_ups_pb2.UtoACommands()
    FinalDest = UtoACommands.dest.add()
    seq_num = get_seqnum()
    FinalDest.seq_num = seq_num
    FinalDest.ship_id = ship_id
    FinalDest.dest_x = final_dest_x
    FinalDest.dest_y = final_dest_y
    print("\nUtoACommands: \n", UtoACommands)
    return seq_num, UtoACommands


#-------------------------------------send message----------------------------------------------

def sendMsg(socket_fd, seq_num, msg, seqnum_dict):
    print("enter sendMsg") 
    serialized_msg = msg.SerializeToString()
    len_prefix = _VarintBytes(len(serialized_msg))
    try:
        with socket_lock:
            socket_fd.sendall(len_prefix + serialized_msg)
            seqnum_dict[seq_num] = msg  # Store the message with its seqnum
    except Exception as e:
        print(f"Failed to send message with seqnum {seq_num}: {e}")


#-----------------------------------------ACK------------------------------------------------


#1. create ACKmsg  2. send ACK  3. add ack(seq_num) to the ACK_list indicate handled
def sendACK_amazon(seq_num, ):
    ACKmsg = amazon_ups_pb2.UtoACommands()
    ACKmsg.acks.append(seq_num)
    print("\nUtoACommands: \n", ACKmsg)
    serialized_msg = ACKmsg.SerializeToString()
    len_prefix = _VarintBytes(len(serialized_msg))
    with socket_lock:
        amazon_fd.sendall(len_prefix+ serialized_msg)
    send_amazon_ACK.append(seq_num)
    print(f"\nthe ACK_list for amazon: {send_amazon_ACK}")
    return

def sendACK_world(seq_num):
    ACKmsg = world_ups_pb2.UCommands()
    ACKmsg.acks.append(seq_num)
    print("\nUCommands: \n", ACKmsg)
    serialized_msg = ACKmsg.SerializeToString()
    len_prefix = _VarintBytes(len(serialized_msg))
    with socket_lock:
        world_fd.sendall(len_prefix+ serialized_msg)
    send_world_ACK.append(seq_num)
    print(f"\nthe ACK_list for world: {send_world_ACK}")
    return

#handle ack, remove the corresponding seqnum and message from the seqnum dictionary 
def handle_ack_from_world(seqnum):
    if seqnum in send_world_seqnum:
        del send_world_seqnum[seqnum]
        print(f"Ack received from World for seqnum: {seqnum}. Now the send_world_seqnum keys: {list(send_world_seqnum.keys())}")


def handle_ack_from_amazon(seqnum):
    if seqnum in send_amazon_seqnum:
        del send_amazon_seqnum[seqnum]
        print(f"Ack received from Amazon for seqnum: {seqnum}. Now the send_amazon_seqnum: {list(send_amazon_seqnum.key())}")

# resend message, check if there is msg without ack receive, if so resend it, use two backend threads
def resend_unack_msg(seqnum_dict,socket_fd):
    while True:
        for seqnum in list(seqnum_dict.keys()): 
            print(f"No ack received for seqnum {seqnum}. Resending...")
            msg = seqnum_dict[seqnum]
            serialized_msg = msg.SerializeToString()
            len_prefix = _VarintBytes(len(serialized_msg))
            with socket_lock:
                socket_fd.sendall(len_prefix + serialized_msg)
        time.sleep(RESEND_MSG_INTERVAL)



#---------------------------------handle query in a seperate thread-----------------------------------------------------

def create_UQuery_msg(truckid):
    UCommands = world_ups_pb2.UCommands()
    UQuery = UCommands.queries.add()
    UQuery.truckid= truckid
    seqnum = get_seqnum()
    UQuery.seqnum= seqnum 
    print(f"UCommands: {UCommands}")
    return seqnum, UCommands

def query_msg(truckid):
    seqnum, msg = create_UQuery_msg(truckid)
    print("Querying truck status:", msg)
    sendMsg(world_fd, seqnum, msg, send_world_seqnum)
    

# def update_truck_statuses(IF_QUERY):
#     while IF_QUERY:
#         for truck_id in range(1, truck_num+1):
#             query_msg(truck_id)
#             time.sleep(UPDATE_INTERVAL)  # Wait some time before querying again


def handle_UTruck(UTruck_msg): #UTruck(truckid, status, x, y, seqnum)
    seq_num = UTruck_msg.seqnum
    if seq_num in send_world_ACK:  #only resend ack
        sendACK_world(seq_num)
        return
    else:
        # 1. sendACK 2. handle_db, update x,y,status of truck
        sendACK_world(seq_num)
        truckid = UTruck_msg.truckid
        x = UTruck_msg.x
        y = UTruck_msg.y
        status = UTruck_msg.status.lower()
        db_UTruck(truckid, x, y, status)

#--------------------------------- main --------------------------------------------------------------    

def main():
    db_delete_all_data()
    global amazon_fd 
    global world_fd
     #  1. as client, connect Amazon, then recv from Amazon
    amazon_fd = create_client_socket(AMAZON_HOST, AMAZON_PORT) 
    print(f"socket with Amazon:{amazon_fd}")

    # 1.recv world id and seq_num 2.connect with world
    msg, world_fd = recv_Amazon_msg(amazon_fd, "ConnectWorldId") 

    # create thread to listen to the Amazon
    amazon_thread = threading.Thread(target=listen_to_amazon, args=(amazon_fd,))
    amazon_thread.start()
    # create thread to listen to the World
    world_thread = threading.Thread(target=listen_to_world, args=(world_fd,))
    world_thread.start()

    # Start a background thread to periodically check and resend unacknowledged messages
    resend_thread = threading.Thread(target=resend_unack_msg, args=(send_amazon_seqnum, amazon_fd))
    resend_thread.daemon = True  # Daemon threads are terminated when the main program exits
    resend_thread.start()

    # Start a background thread to periodically check and resend unacknowledged messages
    resend_thread = threading.Thread(target=resend_unack_msg, args=(send_world_seqnum, world_fd))
    resend_thread.daemon = True  # Daemon threads are terminated when the main program exits
    resend_thread.start()

    # # Starting the continuous update thread
    # query_status_thread = threading.Thread(target=update_truck_statuses, args=(IF_QUERY,))
    # query_status_thread.daemon = True  
    # query_status_thread.start()


# if __name__ == "__main__":
#     main()


