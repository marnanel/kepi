# Generated by Django 2.2.4 on 2020-03-31 01:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trilby_api', '0024_person_language'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='language',
            field=models.CharField(default='en', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='status',
            name='language',
            field=models.CharField(default='en', max_length=255, null=True),
        ),
    ]