# Generated by Django 3.0.6 on 2020-09-22 00:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('MMcalendar', '0007_auto_20200918_2134'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='categories',
        ),
        migrations.RemoveField(
            model_name='service',
            name='categories',
        ),
        migrations.DeleteModel(
            name='EventCategory',
        ),
    ]
