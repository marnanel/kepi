# Generated by Django 2.2.1 on 2019-07-11 11:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_kepi', '0006_auto_20190709_0441'),
    ]

    operations = [
        migrations.AddField(
            model_name='actor',
            name='f_preferredUsername',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
    ]
