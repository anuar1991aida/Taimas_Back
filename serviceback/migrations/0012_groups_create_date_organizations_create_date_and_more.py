# Generated by Django 4.1.2 on 2023-01-22 09:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serviceback', '0011_childs_create_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='groups',
            name='create_date',
            field=models.DateField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='organizations',
            name='create_date',
            field=models.DateField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='profileuser',
            name='create_date',
            field=models.DateField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='visits',
            name='create_date',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]