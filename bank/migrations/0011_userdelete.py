# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-28 11:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bank', '0010_useraccess_useroperation'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserDelete',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Username', models.CharField(max_length=50)),
            ],
        ),
    ]
