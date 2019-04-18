# Generated by Django 2.1.5 on 2019-04-18 13:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_kepi', '0010_auto_20190410_1442'),
    ]

    operations = [
        migrations.CreateModel(
            name='CachedRemoteUser',
            fields=[
                ('owner', models.URLField(primary_key=True, serialize=False)),
                ('key', models.TextField(default=None, null=True)),
                ('inbox', models.URLField()),
                ('outbox', models.URLField()),
            ],
        ),
        migrations.DeleteModel(
            name='CachedPublicKey',
        ),
    ]
