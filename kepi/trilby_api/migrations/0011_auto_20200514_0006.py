# Generated by Django 3.0.4 on 2020-05-14 00:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trilby_api', '0010_remoteperson_hostname'),
    ]

    operations = [
        migrations.AlterField(
            model_name='remoteperson',
            name='url',
            field=models.URLField(default='', max_length=255, unique=True),
            preserve_default=False,
        ),
    ]
