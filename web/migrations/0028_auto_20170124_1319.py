# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-01-24 13:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0027_resource_event_facilitator'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='event_directions',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
