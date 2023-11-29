# Generated by Django 4.1.2 on 2023-01-30 10:37

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serviceback', '0025_rename_imageurl_visits_image_url_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='childs',
            name='child_image',
        ),
        migrations.AddField(
            model_name='childs',
            name='image_url',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='childs',
            name='create_date',
            field=models.DateField(blank=None, default=datetime.datetime(2023, 1, 30, 10, 37, 19, 387520), null=None),
        ),
        migrations.AlterField(
            model_name='visits',
            name='create_date',
            field=models.DateTimeField(blank=None, default=datetime.datetime(2023, 1, 30, 10, 37, 19, 418766), null=None),
        ),
    ]
