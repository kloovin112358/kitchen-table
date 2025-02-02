# Generated by Django 5.1.4 on 2025-01-03 15:44

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_postentry_status_alter_secretsignupcode_code'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='postcategory',
            options={'ordering': ['category']},
        ),
        migrations.CreateModel(
            name='ImageUpload',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uploaded_image', models.ImageField(upload_to='')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('caption', models.CharField(blank=True, max_length=200, null=True)),
                ('related_post_entry', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.postentry')),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.DeleteModel(
            name='MediaUpload',
        ),
    ]
