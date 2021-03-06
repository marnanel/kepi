# Generated by Django 3.0.7 on 2020-06-17 18:42

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('bowler_pub', '0002_delete_fetch'),
    ]

    operations = [
        migrations.CreateModel(
            name='IncomingMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('received_date', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.CharField(default='', max_length=255)),
                ('date', models.CharField(default='', max_length=255)),
                ('host', models.CharField(default='', max_length=255)),
                ('path', models.CharField(default='', max_length=255)),
                ('signature', models.CharField(default='', max_length=255)),
                ('body', models.TextField(default='')),
                ('digest', models.CharField(default='', max_length=255)),
                ('is_local_user', models.BooleanField(default=False)),
            ],
        ),
    ]
