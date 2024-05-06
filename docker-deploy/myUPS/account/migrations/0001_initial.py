# Generated by Django 4.2.10 on 2024-04-22 21:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Package',
            fields=[
                ('packageid', models.IntegerField(primary_key=True, serialize=False)),
                ('dest_x', models.IntegerField()),
                ('dest_y', models.IntegerField()),
                ('status', models.CharField(choices=[('created', 'CREATED'), ('truck en route to warehouse', 'TRUCK_EN_ROUTE_TO_WAREHOUSE'), ('truck waiting for package', 'TRUCK_WAITING_FOR_PACKAGE'), ('out for delivery', 'OUT_FOR_DELIVERY'), ('delivered', 'DELIVERED')], default='unready', max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='Warehouse',
            fields=[
                ('whid', models.IntegerField(primary_key=True, serialize=False)),
                ('x', models.IntegerField()),
                ('y', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Truck',
            fields=[
                ('truckid', models.IntegerField(primary_key=True, serialize=False)),
                ('current_x', models.IntegerField()),
                ('current_y', models.IntegerField()),
                ('status', models.CharField(choices=[('idle', 'IDLE'), ('traveling', 'TRAVELING'), ('arrive warehouse', 'ARRIVE WAREHOUSE'), ('loading', 'LOADING'), ('delivering', 'DELIVERING')], default='idle', max_length=32)),
                ('current_whid', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='account.warehouse')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('product_id', models.IntegerField()),
                ('description', models.CharField(max_length=100)),
                ('count', models.IntegerField()),
                ('packageid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='account.package')),
            ],
        ),
        migrations.AddField(
            model_name='package',
            name='truckid',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='account.truck'),
        ),
        migrations.AddField(
            model_name='package',
            name='user_id',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='package',
            name='whid',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.warehouse'),
        ),
    ]