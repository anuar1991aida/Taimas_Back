# Generated by Django 4.1.2 on 2023-08-18 11:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('serviceback', '0061_visits_hostname'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='visits',
            name='hostname',
        ),
    ]
