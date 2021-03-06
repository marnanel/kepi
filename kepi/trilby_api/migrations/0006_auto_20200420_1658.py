# Generated by Django 3.0.4 on 2020-04-20 16:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trilby_api', '0005_auto_20200415_1658'),
    ]

    operations = [
        migrations.AlterField(
            model_name='follow',
            name='follower',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='rel_following', to='trilby_api.Person'),
        ),
        migrations.AlterField(
            model_name='follow',
            name='following',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='rel_followers', to='trilby_api.Person'),
        ),
    ]
