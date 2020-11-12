# Generated by Django 3.0.9 on 2020-10-29 03:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trilby_api', '0027_localperson_gone'),
    ]

    operations = [
        migrations.CreateModel(
            name='Mention',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='trilby_api.Status')),
                ('whom', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='trilby_api.Person')),
            ],
        ),
        migrations.AddConstraint(
            model_name='mention',
            constraint=models.UniqueConstraint(fields=('status', 'whom'), name='mention_unique'),
        ),
    ]