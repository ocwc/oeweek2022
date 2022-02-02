# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2022-01-17 21:56
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import taggit.managers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('wp_id', models.IntegerField()),
                ('name', models.CharField(max_length=255)),
                ('slug', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('subject', models.CharField(max_length=255)),
                ('body', models.TextField(help_text='You can use the following variables in body and title: {{title}}, {{name}}, {{link}}. HTML is not allowed. ')),
            ],
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=255)),
                ('content', models.TextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('status', models.CharField(choices=[('new', 'New Entry'), ('feedback', 'Requested feedback'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='new', max_length=16)),
                ('post_type', models.CharField(choices=[('resource', 'Resource'), ('project', 'Project'), ('event', 'Event')], max_length=25)),
                ('post_status', models.CharField(choices=[('publish', 'Publish'), ('draft', 'Draft'), ('trash', 'Trash')], max_length=25)),
                ('post_id', models.IntegerField(default=0)),
                ('title', models.CharField(max_length=255)),
                ('slug', models.CharField(blank=True, max_length=255)),
                ('content', models.TextField(blank=True)),
                ('form_id', models.IntegerField(blank=True, null=True)),
                ('contact', models.CharField(blank=True, max_length=255)),
                ('firstname', models.CharField(blank=True, max_length=255, null=True)),
                ('lastname', models.CharField(blank=True, max_length=255, null=True)),
                ('email', models.CharField(blank=True, max_length=255, null=True)),
                ('institution', models.CharField(blank=True, max_length=255, null=True)),
                ('institution_url', models.CharField(blank=True, max_length=255, null=True)),
                ('form_language', models.CharField(blank=True, max_length=255)),
                ('license', models.CharField(blank=True, max_length=255, null=True)),
                ('link', models.CharField(blank=True, max_length=255, null=True)),
                ('linkwebroom', models.CharField(blank=True, max_length=255, null=True)),
                ('image_url', models.URLField(blank=True, max_length=500, null=True)),
                ('city', models.CharField(blank=True, max_length=255)),
                ('country', models.CharField(blank=True, max_length=255)),
                ('event_time', models.DateTimeField(blank=True, null=True)),
                ('event_type', models.CharField(blank=True, choices=[('conference/forum/discussion', 'Conference/forum/discussion'), ('conference/seminar', 'Conference/seminar'), ('workshop', 'Workshop'), ('forum/panel/discussion', 'Forum/panel/discussion'), ('other_local', 'other_local'), ('local', 'local'), ('webinar', 'Webinar'), ('discussion', 'Online Discussion'), ('other_online', 'Other - Online'), ('online', 'Online Event'), ('anytime', 'Anytime Event')], max_length=255, null=True)),
                ('event_online', models.BooleanField(default=False)),
                ('event_source_datetime', models.CharField(blank=True, max_length=255)),
                ('event_source_timezone', models.CharField(blank=True, max_length=255)),
                ('event_directions', models.CharField(blank=True, max_length=255, null=True)),
                ('event_other_text', models.CharField(blank=True, max_length=255, null=True)),
                ('event_facilitator', models.CharField(blank=True, max_length=255, null=True)),
                ('archive_planned', models.BooleanField(default=False)),
                ('archive_link', models.CharField(blank=True, max_length=255)),
                ('lat', models.FloatField(blank=True, null=True)),
                ('lng', models.FloatField(blank=True, null=True)),
                ('address', models.CharField(blank=True, max_length=1024)),
                ('opentags', models.CharField(blank=True, max_length=255)),
                ('notified', models.BooleanField(default=False)),
                ('raw_post', models.TextField(blank=True)),
                ('screenshot_status', models.CharField(blank=True, default='', max_length=64)),
                ('year', models.IntegerField(blank=True, default=2021, null=True)),
                ('oeaward', models.BooleanField(default=False)),
                ('twitter', models.CharField(blank=True, max_length=255, null=True)),
                ('categories', models.ManyToManyField(blank=True, to='web.Category')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ResourceImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, upload_to='images/')),
            ],
        ),
        migrations.AddField(
            model_name='resource',
            name='image',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='web.ResourceImage'),
        ),
        migrations.AddField(
            model_name='resource',
            name='reviewer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='resource',
            name='tags',
            field=taggit.managers.TaggableManager(blank=True, help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
    ]
