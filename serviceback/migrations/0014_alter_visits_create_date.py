# Generated by Django 4.1.2 on 2023-01-20 09:46

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serviceback', '0013_alter_visits_create_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='visits',
            name='create_date',
            field=models.DateTimeField(default=datetime.datetime(2023, 1, 20, 14, 46, 39, 486328), null=True),
        ),
    ]
