# Generated by Django 5.1.6 on 2025-03-01 14:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('embeddings', '0002_alter_parrafo_proyecto_alter_parrafo_texto'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Parrafo',
        ),
    ]
