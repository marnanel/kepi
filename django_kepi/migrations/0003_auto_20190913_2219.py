# Generated by Django 2.2.4 on 2019-09-13 22:19

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('django_kepi', '0002_acobject_published_squashed_0003_auto_20190913_2151'),
    ]

    operations = [
        migrations.AlterField(
            model_name='acobject',
            name='published',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
