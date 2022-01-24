# Generated by Django 3.0.6 on 2020-10-06 21:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MMUX', '0008_relationship_revoked'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='mailingList',
        ),
        migrations.AddField(
            model_name='profile',
            name='image',
            field=models.URLField(blank=True, null=True),
        ),
    ]