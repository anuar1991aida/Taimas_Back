# Generated by Django 4.1.2 on 2023-05-11 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serviceback', '0049_descriptors_id_face1024'),
    ]

    operations = [
        migrations.AddField(
            model_name='descriptors',
            name='id_face128',
            field=models.TextField(default='', null=True),
        ),
    ]
