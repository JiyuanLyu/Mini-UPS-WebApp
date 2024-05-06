from django.db import models
from django.contrib.auth.models import User

class Warehouse(models.Model):
    whid = models.IntegerField(primary_key=True)
    x = models.IntegerField()
    y = models.IntegerField() 
    
class Truck(models.Model):
    truckid = models.IntegerField(primary_key=True)
    current_x = models.IntegerField()
    current_y = models.IntegerField()
    current_whid = models.ForeignKey(Warehouse, null=True, on_delete=models.SET_NULL)
    status_options = (
        ('idle', 'idle'),
        ('traveling', 'traveling'),
        ('arrive warehouse', 'arrive warehouse'),
        ('loading', 'loading'),
        ('delivering', 'delivering')
    )
    status = models.CharField(max_length=32, choices=status_options, default="idle")

class Package(models.Model):
    packageid = models.IntegerField(primary_key=True)
    whid = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    truckid = models.ForeignKey(Truck, null=True, on_delete=models.SET_NULL)
    dest_x = models.IntegerField()
    dest_y = models.IntegerField()
    status_options = (
        ('created', 'created'),
        ('truck en route to warehouse', 'truck en route to warehouse'),
        ('truck waiting for package', 'truck waiting for package'),
        ('out for delivery', 'out for delivery'),
        ('delivered','delivered')
    )
    status = models.CharField(max_length=32, choices=status_options, default= 'created')
    user_id = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    product_id = models.IntegerField()
    description = models.CharField(max_length=100)
    count = models.IntegerField()
    packageid = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='products')
#package.products.all()