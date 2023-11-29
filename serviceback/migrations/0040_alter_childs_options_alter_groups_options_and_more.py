# Generated by Django 4.1.2 on 2023-03-31 17:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serviceback', '0039_groups_category'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='childs',
            options={'ordering': ['name'], 'verbose_name': 'Ребенок', 'verbose_name_plural': 'Дети'},
        ),
        migrations.AlterModelOptions(
            name='groups',
            options={'ordering': ['group_name'], 'verbose_name': 'Группа', 'verbose_name_plural': 'Группы'},
        ),
        migrations.AlterModelOptions(
            name='organizations',
            options={'ordering': ['org_name'], 'verbose_name': 'Организация', 'verbose_name_plural': 'Организации'},
        ),
        migrations.AlterModelOptions(
            name='profileuser',
            options={'ordering': ['name'], 'verbose_name': 'Пользователь', 'verbose_name_plural': 'Пользователи'},
        ),
        migrations.AlterModelOptions(
            name='regions',
            options={'ordering': ['name'], 'verbose_name': 'Регион', 'verbose_name_plural': 'Регионы'},
        ),
        migrations.AddField(
            model_name='organizations',
            name='id_obl',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='organizations',
            name='id_region',
            field=models.BigIntegerField(default=0),
        ),
    ]
