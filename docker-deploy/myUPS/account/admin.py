from django.contrib import admin
from .models import Truck, Warehouse, Package, Product


admin.site.register(Truck)
admin.site.register(Warehouse)
admin.site.register(Package)
admin.site.register(Product)