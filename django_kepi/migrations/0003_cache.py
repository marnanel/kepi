# Generated by Django 2.1.2 on 2018-10-29 08:41

from django.db import migrations, models
import django_kepi.cache_model


class Migration(migrations.Migration):

    dependencies = [
        ('django_kepi', '0002_auto_20181029_0829'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cache',
            fields=[
                ('url', models.URLField(max_length=255, primary_key=True, serialize=False)),
                ('f_type', models.CharField(blank=True, max_length=255)),
                ('value', models.TextField(blank=True, max_length=1048576)),
                ('stale_date', models.URLField(blank=True, default=django_kepi.cache_model.cache_expiry_time)),
            ],
        ),
    ]
