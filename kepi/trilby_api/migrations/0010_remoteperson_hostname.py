# Generated by Django 3.0.4 on 2020-05-11 19:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trilby_api', '0009_auto_20200511_1853'),
    ]

    operations = [
        migrations.AddField(
            model_name='remoteperson',
            name='hostname',
            field=models.CharField(default='', max_length=255),
        ),
    ]