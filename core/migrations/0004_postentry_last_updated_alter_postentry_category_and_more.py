# Generated by Django 5.1.4 on 2025-01-03 16:11

import django.db.models.deletion
import django.utils.timezone
import taggit.managers
import tinymce.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_alter_postcategory_options_imageupload_and_more'),
        ('taggit', '0006_rename_taggeditem_content_type_object_id_taggit_tagg_content_8fc721_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='postentry',
            name='last_updated',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='postentry',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to='core.postcategory'),
        ),
        migrations.AlterField(
            model_name='postentry',
            name='created_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='postentry',
            name='post_body',
            field=tinymce.models.HTMLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='postentry',
            name='status',
            field=models.CharField(choices=[('Live', 'Live'), ('Draft', 'Draft')], default='Draft', max_length=5),
        ),
        migrations.AlterField(
            model_name='postentry',
            name='tags',
            field=taggit.managers.TaggableManager(blank=True, help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
        migrations.AlterField(
            model_name='postentry',
            name='title',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
    ]