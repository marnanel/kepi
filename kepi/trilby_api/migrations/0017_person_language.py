# Generated by Django 3.0.4 on 2020-05-28 21:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trilby_api', '0016_auto_20200525_1608'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='language',
            field=models.CharField(default='en', help_text="The language this user usually posts in. Use an ISO 639 code, such as 'en' or 'cy'.", max_length=16),
        ),
    ]
