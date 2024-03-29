# Generated by Django 4.1.2 on 2023-04-02 01:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serviceback', '0040_alter_childs_options_alter_groups_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizations',
            name='count_place',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='organizations',
            name='name_obl',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='organizations',
            name='name_region',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='organizations',
            name='type_org',
            field=models.CharField(default='pr', max_length=2),
        ),
    ]
