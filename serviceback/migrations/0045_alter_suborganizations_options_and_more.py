# Generated by Django 4.1.2 on 2023-04-18 11:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('serviceback', '0044_weekendday'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='suborganizations',
            options={'verbose_name': 'Организация', 'verbose_name_plural': 'Иерархия организаций'},
        ),
        migrations.RenameField(
            model_name='weekendday',
            old_name='WeekendDate',
            new_name='weekend',
        ),
    ]
