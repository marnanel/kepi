# Generated by Django 2.2.4 on 2020-03-21 18:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trilby_api', '0012_status_remote_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='locked',
            field=models.BooleanField(default=False, help_text="If True, only followers can see this account's statuses."),
        ),
    ]
