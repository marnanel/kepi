# Generated by Django 2.2.4 on 2019-11-16 15:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kepi', '0002_acitem_serial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='acactor',
            old_name='f_publicKey',
            new_name='publicKey',
        ),
    ]
