# Generated by Django 3.0.6 on 2020-09-16 04:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MMcalendar', '0002_service_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=6),
        ),
        migrations.AlterField(
            model_name='service',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=6),
        ),
    ]
