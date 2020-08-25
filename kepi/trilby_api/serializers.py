# serializers.py
#
# Part of kepi, an ActivityPub daemon.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

from rest_framework import serializers
from kepi.trilby_api.models import *
from rest_framework_recursive.fields import RecursiveField
from oauth2_provider.models import Application
import kepi.trilby_api.utils as trilby_utils
import markdown

"""
These are the serialisers for the Mastodon protocol.
"""

#########################################

class UserSerializer(serializers.ModelSerializer):

    id = serializers.CharField(
            read_only = True)

    uri = serializers.CharField(
            read_only = True)

    url = serializers.CharField(
            read_only = True)

    avatar = serializers.URLField(
            source='icon_or_default',
            )
    header = serializers.URLField(
            source='header_or_default',
            )

    avatar_static = serializers.URLField(
            source='icon_or_default',
            )
    header_static = serializers.URLField(
            source='header_or_default',
            )

    username = serializers.CharField(
            )

    display_name = serializers.CharField(
            )

    acct = serializers.CharField(
            )

    created_at = serializers.DateTimeField(
            )

    note = serializers.CharField(
            )

    following_count = serializers.IntegerField(
            read_only = True,
            )
    followers_count = serializers.IntegerField(
            read_only = True,
            )
    statuses_count = serializers.IntegerField(
            read_only = True,
            )

    class Meta:
        model = Person
        fields = (
                'id',
                'uri',
                'url',
                'username',
                'acct',
                'display_name',
                'locked',
                'created_at',
                'followers_count',
                'following_count',
                'statuses_count',
                'note',
                'avatar',
                'avatar_static',
                'header',
                'header_static',
                'moved_to',
                'fields',
                'emojis',
                'bot',
                )

#########################################

class NestedSourceSerializer(UserSerializer):

    class Meta:
        model = UserSerializer.Meta.model
        fields = (
                'privacy',
                'sensitive',
                'note',
                'language',
                )

    privacy = serializers.ChoiceField(
            choices = trilby_utils.VISIBILITY_CHOICES,
            source = 'get_default_visibility_display',
            )

    sensitive = serializers.BooleanField(
            source = 'default_sensitive',
            )

#########################################

class UserSerializerWithSource(UserSerializer):

    class Meta:
        model = UserSerializer.Meta.model
        fields = UserSerializer.Meta.fields + (
            'source',
            )

    source = NestedSourceSerializer(source='*')

#########################################

class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = (
                'id',
                'uri',
                'url',
                'account',
                'in_reply_to_id',
                'in_reply_to_account_id',
                'reblog',
                'content',
                'status',
                'created_at',
                'emojis',
                'reblogs_count',
                'favourites_count',
                'reblogged',
                'favourited',
                'muted',
                'sensitive',
                'spoiler_text',
                'visibility',
                'media_attachments',
                'mentions',
                'tags',
                'card',
                'poll',
                # FIXME: "application" is supposed to be a dict
                # of {name, website}. The app name is held in
                # oauth2_provider, but we don't keep the website
                # anywhere. We could, but it would mean patching
                # an upstream library.
                #
                #'application',
                'language',
                'pinned',
                'idempotency_key',
                )

    def create(self, validated_data):
        posted_by = self.context['request'].user
        validated_data['posted_by'] = posted_by
        validated_data['type'] = 'Note'

        result = bowler_pub_create(
                value = validated_data,
                )

        return result

    id = serializers.SerializerMethodField()

    uri = serializers.URLField(
            read_only = True)

    url = serializers.URLField(
            read_only = True)

    account = UserSerializer(
            )

    in_reply_to_id = serializers.PrimaryKeyRelatedField(
            queryset=Status.objects.all,
            required = False)

    in_reply_to_account_id = serializers.PrimaryKeyRelatedField(
            queryset=Person.objects.all,
            default = None,
            required = False)

    reblog = RecursiveField(
            source = 'reblog_of',
            required = False,
            )

    # "content" is read-only for HTML;
    # "status" is write-only for text (or Markdown)
    content = serializers.SerializerMethodField(
            read_only = True)

    status = serializers.CharField(
            source='source_text',
            write_only = True)

    def get_content(self, status):
        result = markdown.markdown(status.content)
        return result

    created_at = serializers.DateTimeField(
            required = False,
            read_only = True)

   # TODO Media

    sensitive = serializers.BooleanField(
            required = False)
    spoiler_text = serializers.CharField(
            allow_blank = True,
            required = False)

    visibility = serializers.CharField(
            required = False)

    language = serializers.CharField(
            required = False)

    idempotency_key = serializers.CharField(
            write_only = True,
            required = False)

    def get_id(self, status):
        return str(status.id)

class StatusContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = (
                'ancestors',
                'descendants',
                )

    ancestors = StatusSerializer(
            many = True)

    descendants = StatusSerializer(
            many = True)

class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = [
                'id',
                'type',
                'created_at',
                'account',
                'status',
                ]

    account = UserSerializer(source='about_account')

    status = StatusSerializer()

NotificationSerializer._declared_fields['type'] = \
    serializers.CharField(source='get_notification_type_display')
