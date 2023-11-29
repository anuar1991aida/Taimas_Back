# Generated by Django 4.1.2 on 2023-04-19 21:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serviceback', '0046_childs_id_face512'),
    ]

    operations = [
        migrations.CreateModel(
            name='Descriptors',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('iin', models.CharField(max_length=12)),
                ('id_face512', models.TextField(default='', null=True)),
                ('image_url', models.TextField(blank=True, null=True)),
                ('create_date', models.DateField(blank=None, null=True)),
            ],
        ),
    ]
