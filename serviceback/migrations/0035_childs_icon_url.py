# Generated by Django 4.1.2 on 2023-02-22 11:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serviceback', '0034_visits_comments'),
    ]

    operations = [
        migrations.AddField(
            model_name='childs',
            name='icon_url',
            field=models.TextField(blank=True, null=True),
        ),
    ]