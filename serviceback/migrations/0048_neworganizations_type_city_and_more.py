# Generated by Django 4.1.2 on 2023-04-21 16:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serviceback', '0047_descriptors'),
    ]

    operations = [
        migrations.AddField(
            model_name='neworganizations',
            name='type_city',
            field=models.CharField(blank=True, default='gor', max_length=4, null=True),
        ),
        migrations.AddField(
            model_name='neworganizations',
            name='type_ecolog',
            field=models.CharField(blank=True, default='normal', max_length=6, null=True),
        ),
        migrations.AddField(
            model_name='organizations',
            name='type_city',
            field=models.CharField(blank=True, default='gor', max_length=4, null=True),
        ),
        migrations.AddField(
            model_name='organizations',
            name='type_ecolog',
            field=models.CharField(blank=True, default='normal', max_length=6, null=True),
        ),
    ]
