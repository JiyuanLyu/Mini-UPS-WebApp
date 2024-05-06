import os
import django
# import world_ups_pb2 
# import amazon_ups_pb2 
# from django.db.models import Q
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myUPS.settings")
django.setup()


from account.models import *
from django.db import IntegrityError
from django.db import transaction
#---------------------------------------- db handle msg ------------------------------------------------------------

#TODO: if delete User
def db_delete_all_data():
    try:
        with transaction.atomic():
            # Deletes all instances of each model
            Product.objects.all().delete()
            Package.objects.all().delete()
            Truck.objects.all().delete()
            Warehouse.objects.all().delete()
            print("All data has been deleted successfully.")
    except Exception as e:
        print(f"An error occurred while deleting the data: {e}")


def db_init_truck(truck_num):
    try:
        for i in range(1, truck_num + 1):
            truck = Truck(truckid=i, current_x=0, current_y=0, current_whid=None, status="idle")
            truck.save()
    except IntegrityError as e:
        # Handle the integrity error, such as logging the error or printing a message
        print(f"IntegrityError occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")



def db_RequestTruck(whid, warehouse_x, warehouse_y, truckid, packageid, dest_x, dest_y, user_id=None, products=None):

    # handle Warehouse
    warehouse, created = Warehouse.objects.get_or_create(
        whid=whid,
        defaults={'x': warehouse_x, 'y': warehouse_y}
    )

    # handle truck
    try:
        truck = Truck.objects.get(pk=truckid)
    except Truck.DoesNotExist:
        print(f"Truck with ID {truckid} does not exist.")
        return

    # Handle Package
    package = Package.objects.create(
        packageid=packageid,
        whid=warehouse,
        truckid=truck,
        dest_x=dest_x,
        dest_y=dest_y,
        status='created'
    )
    
    # handle user
    if user_id:
        try:
            user = User.objects.get(pk=user_id)
            package.user_id = user  # Associate the user with the package
        except User.DoesNotExist:
            print(f"User with ID {user_id} does not exist.")
   
    # handle products
    if products:
        for product_id, description, count in products:
            product = Product.objects.create(
                product_id=product_id, 
                description=description, 
                count=count,
                packageid=package  # Associate the product with the package
            )
            print(f"Added product {product_id}, name {description} to package {packageid} with count {count}")
            product.save()      
    package.save()
    print("success db_RequestTruck ")  


# #TODO: 1. if use update_or_create, get_or_create or create()  2. modify status
# def db_RequestTruck(RequestTruck_msg, whid,warehouse_x, warehouse_y, truckid):

#     print("enter the requestTruck")
   
#     print (f"enter whid1: ,{whid}")
#     warehouse, created = Warehouse.objects.get_or_create(
#         whid=whid,
#         defaults={'x': warehouse_x, 'y': warehouse_y}
#     )
#     whid2 = warehouse.whid
#     print (f"enter whid2: ,{whid2}")

#     # #  Handle Warehouse
#     # print("enter the requestTruck")
#     # whid = RequestTruck_msg.whid
#     # print (f"enter whid1: ,{whid}")
#     # warehouse, created = Warehouse.objects.get_or_create(
#     #     whid=RequestTruck_msg.whid,
#     #     defaults={'x': RequestTruck_msg.warehouse_x, 'y': RequestTruck_msg.warehouse_y}
#     # )
#     # whid2 = warehouse.whid
#     # print (f"enter whid2: ,{whid2}")
#     # handle truck
#     try:
#         truck = Truck.objects.get(pk=truckid)
#     except Truck.DoesNotExist:
#         print(f"Truck with ID {truckid} does not exist.")
#         return
#     print (f"enter truckid: ,{truckid}")
#     # Handle Package
#     package = Package.objects.create(
#         packageid=RequestTruck_msg.ship_id,
#         whid=warehouse,
#         truckid=truck,
#         dest_x=RequestTruck_msg.dest_x,
#         dest_y=RequestTruck_msg.dest_y,
#         status='created'
#     )
#     print("first create package without id")
#     # Handle User
#     user = None
#     if hasattr(RequestTruck_msg, 'ups_order') and RequestTruck_msg.ups_order.UPSuserId.isdigit():
#         try:
#             user = User.objects.get(pk=int(RequestTruck_msg.ups_order.UPSuserId))
#         except User.DoesNotExist:
#             print(f"User with ID {RequestTruck_msg.ups_order.UPSuserId} does not exist.")
#     if user:
#         package.user_id = user
#         package.save()
#     print("handle user ")
#     # Handle Products
#     if hasattr(RequestTruck_msg, 'ups_order'):
#         for a_product in RequestTruck_msg.ups_order.product:
#             product = Product.objects.create(
#                 product_id=a_product.id,
#                 package=package,
#                 description=a_product.description,
#                 count=a_product.count
#             )
#             product.save()
#     print("handle product ")       
#     package.save()
#     print("package done")    



def db_UFinished(truckid, x, y, whid):
    try:
        truck = Truck.objects.get(pk=truckid)
        truck.current_x = x
        truck.current_y = y
        warehouse = Warehouse.objects.get(pk=whid)
        truck.current_whid = warehouse
        truck.status = 'arrive warehouse'
        truck.save()
        print ("exit db_Ufinished")
    except truck.DoesNotExist:
        print("Truck does not exist")



#TODO: if need ??
def db_UFinished_idle(truckid, x, y):
    truck = Truck.objects.get(pk=truckid)
    truck.current_x = x
    truck.current_y = y
    truck.current_whid = None
    truck.status == "idle"
    truck.save()


def db_UTruck(truckid, x, y, status):
    try:
        truck = Truck.objects.get(pk=truckid)
        truck.current_x = x
        truck.current_y = y
        truck.status = status
        truck.save()
    except truck.DoesNotExist:
        print("Truck does not exist")


#handle 1. package status delivered 
#TODO: ????2. truck status
# def db_UDeliveryMade(truckid, packageid):
def db_UDeliveryMade(packageid):
    try:
        package = Package.objects.get(packageid=packageid)
        package.status = "delivered"
        package.save()
    except Package.DoesNotExist:
        print(f"No package found with package ID {packageid}")




#--------------------------------------------- db modify ------------------------------------------------------------
def db_modify_package_status(packageid, status_str):
    try:
        package = Package.objects.get(pk=packageid)
        if status_str in dict(package._meta.get_field('status').choices).values():
            package.status = status_str
            package.save()
        else:
            print(f"Invalid status: {status_str}. Available options: {[choice[1] for choice in package.status_options]}")
    except Package.DoesNotExist:
        print(f"No package found with package ID {packageid}")

def db_modify_truck_status(truckid, status_str):
    try:
        truck = Truck.objects.get(pk=truckid)
        if status_str in dict(truck._meta.get_field('status').choices).values():
            truck.status = status_str
            truck.save()
        else:
            print(f"Invalid status: {status_str}. Available options: {[choice[1] for choice in truck.status_options]}")
    except Package.DoesNotExist:
        print(f"No truck found with truck ID {truckid}")

# ----------------------------------------db get ------------------------------------------------------------
def db_getWhid(packageid):
    try:
        package = Package.objects.get(pk = packageid)
        warehouse = package.whid
        return warehouse.whid
    except Package.DoesNotExist:
        return None  

def db_getPackage_status(packageid):
    try:
        package = Package.objects.get(pk = packageid)
        return package.status
    except Package.DoesNotExist:
        return None  

def db_getTruckid(packageid):
    try:
        package = Package.objects.get(pk=packageid) 
        truck = package.truckid  
        return truck.truckid  
    except Package.DoesNotExist:
        return None  


def db_convertWhid(x, y):
    try:
        # Retrieve the Warehouse object based on x and y coordinates
        warehouse = Warehouse.objects.get(x=x, y=y)
        return warehouse.whid
    except Warehouse.DoesNotExist:
        print("Warehouse does not exist with the given coordinates")
        return None
    
def db_getLocation(packageid):
    packages = Package.objects.filter(pk = packageid)
    package_info = [(package.packageid, package.dest_x, package.dest_y) for package in packages]
    return package_info


# ----------------------------------------db find ------------------------------------------------------------

def db_findPackage_waiting_truck(truckid, whid):
    # Query the Package objects with the specified truckid, whid, and status
    packages = Package.objects.filter(truckid= truckid, whid=whid, status='truck en route to warehouse')
    
    if packages.exists():
        # Extract and return a list of tuples
        truck = Truck.objects.get(pk = truckid)
        truck_id = truck.truckid
        package_info = [(package.packageid, truck_id) for package in packages]
        return package_info
    else:
        return None  
    


def db_find_truck_pickup(whid):
    while True:
        try:
            # First choice: trucks available in the same warehouse with status 'arrive warehouse'
            same_warehouse_trucks = Truck.objects.filter(
                current_whid=whid,
                status='arrive warehouse'
            )
            if same_warehouse_trucks.exists():
                truck = same_warehouse_trucks.first()
                return truck.truckid

            # Trucks with status 'idle' and no whid( all jobs finished)
            idle_trucks = Truck.objects.filter(status='idle', current_whid=None)
            if idle_trucks.exists():
                truck = idle_trucks.first()
                return truck.truckid

            # Trucks with status 'delivering'
            delivering_trucks = Truck.objects.filter(status__in=['idle','delivering'])
            if delivering_trucks.exists():
                truck = delivering_trucks.first()
                return truck.truckid

            # Wait for 2 seconds before retrying
            time.sleep(2)
        except Exception as e:
            print(f"Error occurred when finding Truck to pick up: {e}")
            return None

