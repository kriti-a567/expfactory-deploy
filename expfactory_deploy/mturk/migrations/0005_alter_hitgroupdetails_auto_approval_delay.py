# Generated by Django 4.1.3 on 2023-05-02 19:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mturk", "0004_alter_hitgroup_details"),
    ]

    operations = [
        migrations.AlterField(
            model_name="hitgroupdetails",
            name="auto_approval_delay",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
