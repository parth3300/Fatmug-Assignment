# Generated by Django 5.0.4 on 2024-05-08 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0003_alter_vender_average_response_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vender',
            name='average_response_time',
            field=models.FloatField(default=0),
        ),
    ]
