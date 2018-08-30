# Generated by Django 2.1 on 2018-08-30 13:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('django_kepi', '0007_auto_20180829_1550'),
    ]

    operations = [
        migrations.RenameField(
            model_name='requestingaccess',
            old_name='hopefuls',
            new_name='hopeful',
        ),
        migrations.AlterField(
            model_name='requestingaccess',
            name='grantor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grantors', to='django_kepi.Actor'),
        ),
    ]
