# Generated by Django 2.2.4 on 2019-10-09 15:38

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='AcObject',
            fields=[
                ('id', models.CharField(default=None, editable=False, max_length=255, primary_key=True, serialize=False, unique=True)),
                ('published', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_kepi.acobject_set+', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
        ),
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.URLField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Fetch',
            fields=[
                ('url', models.URLField(primary_key=True, serialize=False)),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='Following',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('follower', models.URLField(max_length=255)),
                ('following', models.URLField(max_length=255)),
                ('pending', models.BooleanField(default=True)),
            ],
        ),
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
        migrations.CreateModel(
            name='AcActivity',
            fields=[
                ('acobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcObject')),
                ('f_actor', models.CharField(blank=True, default=None, max_length=255, null=True)),
            ],
            options={
                'verbose_name': 'activity',
                'verbose_name_plural': 'activities',
            },
            bases=('kepi.acobject',),
        ),
        migrations.CreateModel(
            name='AcActor',
            fields=[
                ('acobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcObject')),
                ('privateKey', models.TextField(blank=True, null=True)),
                ('f_name', models.TextField(help_text='Your name, in human-friendly form. Something like "Alice Liddell".', verbose_name='name')),
                ('f_publicKey', models.TextField(blank=True, null=True, verbose_name='public key')),
                ('auto_follow', models.BooleanField(default=True, help_text='If True, follow requests will be accepted automatically.')),
                ('f_summary', models.TextField(default='', help_text='Your biography. Something like "I enjoy falling down rabbitholes."', max_length=255, verbose_name='bio')),
                ('icon', models.ImageField(help_text='A small square image used to identify you.', null=True, upload_to='', verbose_name='icon')),
                ('header', models.ImageField(help_text="A large image, wider than it's tall, which appears at the top of your profile page.", null=True, upload_to='', verbose_name='header image')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acobject',),
        ),
        migrations.CreateModel(
            name='AcItem',
            fields=[
                ('acobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcObject')),
                ('f_content', models.CharField(blank=True, max_length=255)),
                ('f_attributedTo', models.CharField(blank=True, max_length=255)),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acobject',),
        ),
        migrations.CreateModel(
            name='ThingField',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field', models.CharField(max_length=255)),
                ('value', models.CharField(blank=True, default=None, max_length=255, null=True)),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='kepi.AcObject')),
            ],
        ),
        migrations.CreateModel(
            name='Mention',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('to_actor', models.CharField(max_length=255)),
                ('from_status', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='kepi.AcObject')),
            ],
        ),
        migrations.CreateModel(
            name='CollectionMember',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='kepi.AcObject')),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='kepi.Collection')),
            ],
        ),
        migrations.CreateModel(
            name='Audience',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field', models.PositiveSmallIntegerField(choices=[(1, 'audience'), (2, 'to'), (4, 'cc'), (114, 'bto'), (116, 'bcc')])),
                ('recipient', models.CharField(max_length=255)),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='kepi.AcObject')),
            ],
        ),
        migrations.CreateModel(
            name='AcAccept',
            fields=[
                ('acactivity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcActivity')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acactivity',),
        ),
        migrations.CreateModel(
            name='AcAdd',
            fields=[
                ('acactivity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcActivity')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acactivity',),
        ),
        migrations.CreateModel(
            name='AcAnnounce',
            fields=[
                ('acactivity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcActivity')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acactivity',),
        ),
        migrations.CreateModel(
            name='AcApplication',
            fields=[
                ('acactor_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcActor')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acactor',),
        ),
        migrations.CreateModel(
            name='AcArticle',
            fields=[
                ('acitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcItem')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acitem',),
        ),
        migrations.CreateModel(
            name='AcAudio',
            fields=[
                ('acitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcItem')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acitem',),
        ),
        migrations.CreateModel(
            name='AcCreate',
            fields=[
                ('acactivity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcActivity')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acactivity',),
        ),
        migrations.CreateModel(
            name='AcDelete',
            fields=[
                ('acactivity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcActivity')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acactivity',),
        ),
        migrations.CreateModel(
            name='AcDocument',
            fields=[
                ('acitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcItem')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acitem',),
        ),
        migrations.CreateModel(
            name='AcEvent',
            fields=[
                ('acitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcItem')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acitem',),
        ),
        migrations.CreateModel(
            name='AcFollow',
            fields=[
                ('acactivity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcActivity')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acactivity',),
        ),
        migrations.CreateModel(
            name='AcGroup',
            fields=[
                ('acactor_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcActor')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acactor',),
        ),
        migrations.CreateModel(
            name='AcImage',
            fields=[
                ('acitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcItem')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acitem',),
        ),
        migrations.CreateModel(
            name='AcLike',
            fields=[
                ('acactivity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcActivity')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acactivity',),
        ),
        migrations.CreateModel(
            name='AcNote',
            fields=[
                ('acitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcItem')),
            ],
            options={
                'verbose_name': 'note',
            },
            bases=('kepi.acitem',),
        ),
        migrations.CreateModel(
            name='AcOrganization',
            fields=[
                ('acactor_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcActor')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acactor',),
        ),
        migrations.CreateModel(
            name='AcPage',
            fields=[
                ('acitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcItem')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acitem',),
        ),
        migrations.CreateModel(
            name='AcPerson',
            fields=[
                ('acactor_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcActor')),
            ],
            options={
                'verbose_name': 'person',
                'verbose_name_plural': 'people',
            },
            bases=('kepi.acactor',),
        ),
        migrations.CreateModel(
            name='AcPlace',
            fields=[
                ('acitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcItem')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acitem',),
        ),
        migrations.CreateModel(
            name='AcProfile',
            fields=[
                ('acitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcItem')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acitem',),
        ),
        migrations.CreateModel(
            name='AcReject',
            fields=[
                ('acactivity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcActivity')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acactivity',),
        ),
        migrations.CreateModel(
            name='AcRelationship',
            fields=[
                ('acitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcItem')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acitem',),
        ),
        migrations.CreateModel(
            name='AcRemove',
            fields=[
                ('acactivity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcActivity')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acactivity',),
        ),
        migrations.CreateModel(
            name='AcService',
            fields=[
                ('acactor_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcActor')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acactor',),
        ),
        migrations.CreateModel(
            name='AcUndo',
            fields=[
                ('acactivity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcActivity')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acactivity',),
        ),
        migrations.CreateModel(
            name='AcUpdate',
            fields=[
                ('acactivity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcActivity')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acactivity',),
        ),
        migrations.CreateModel(
            name='AcVideo',
            fields=[
                ('acitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='kepi.AcItem')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('kepi.acitem',),
        ),
        migrations.AddConstraint(
            model_name='thingfield',
            constraint=models.UniqueConstraint(fields=('parent', 'field'), name='parent_field'),
        ),
        migrations.AddField(
            model_name='collection',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='kepi.AcActor'),
        ),
        migrations.AddConstraint(
            model_name='collection',
            constraint=models.UniqueConstraint(fields=('owner', 'name'), name='owner and name'),
        ),
    ]