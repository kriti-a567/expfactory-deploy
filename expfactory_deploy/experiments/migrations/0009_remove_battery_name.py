# Generated by Django 3.1.7 on 2021-10-29 18:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0008_battery_name2'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='battery',
            name='name',
        ),
    ]
