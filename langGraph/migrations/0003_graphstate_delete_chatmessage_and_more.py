# Generated by Django 5.1.7 on 2025-03-13 14:06

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('langGraph', '0002_chatmessage_additional_kwargs_chatmessage_is_summary_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GraphState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('thread_id', models.CharField(max_length=255, unique=True)),
                ('state', models.JSONField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.DeleteModel(
            name='ChatMessage',
        ),
        migrations.AddIndex(
            model_name='graphstate',
            index=models.Index(fields=['thread_id'], name='langGraph_g_thread__ee2753_idx'),
        ),
        migrations.AddIndex(
            model_name='graphstate',
            index=models.Index(fields=['user', 'thread_id'], name='langGraph_g_user_id_4d56b8_idx'),
        ),
    ]
