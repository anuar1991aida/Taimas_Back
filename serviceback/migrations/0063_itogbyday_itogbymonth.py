# Generated by Django 4.1.2 on 2023-08-31 23:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serviceback', '0062_remove_visits_hostname'),
    ]

    operations = [
        migrations.CreateModel(
            name='ItogByDay',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datestatus', models.DateField(db_index=True, null=True)),
                ('id_org', models.CharField(db_index=True, max_length=15)),
                ('visit', models.IntegerField(default=0)),
                ('boln', models.IntegerField(default=0)),
                ('otpusk', models.IntegerField(default=0)),
                ('notvisit', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='ItogByMonth',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datestatus', models.DateField(db_index=True, null=True)),
                ('id_org', models.CharField(db_index=True, max_length=15)),
                ('visit', models.IntegerField(default=0)),
                ('boln', models.IntegerField(default=0)),
                ('otpusk', models.IntegerField(default=0)),
                ('notvisit', models.IntegerField(default=0)),
            ],
        ),
    ]
