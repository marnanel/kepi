# Generated by Django 3.0.4 on 2020-04-15 15:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trilby_api', '0003_auto_20200414_1634'),
    ]

    operations = [
        migrations.AddField(
            model_name='status',
            name='reblog_of',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reblogs', to='trilby_api.Status'),
        ),
        migrations.AlterField(
            model_name='status',
            name='in_reply_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='replies', to='trilby_api.Status'),
        ),
    ]