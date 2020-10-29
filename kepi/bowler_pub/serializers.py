# serializers.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
These are the serialisers for ActivityPub.
"""
import logging
logger = logging.getLogger(name="kepi")

from rest_framework import serializers
import kepi.trilby_api.models as trilby_models
from rest_framework_recursive.fields import RecursiveField
from rest_framework_constant.fields import ConstantField
from kepi.bowler_pub.utils import uri_to_url
from django.conf import settings

#########################################

class StatusObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = trilby_models.Status

    def to_representation(self, status):

        replies = [
                StatusObjectSerializer(x).data()
                for x in status.replies.all()]

        return {
                'id': status.url,
                'url': status.url,
                'type': 'Note',
                'summary': status.spoiler_text,
                'inReplyTo': status.in_reply_to,
                'published': status.created_at,
                'attributedTo': status.account.url,
                'to': status.to,
                'cc': status.cc,
                'sensitive': status.sensitive,
                'conversation': status.conversation,
                'content': status.content,
                'contentMap': {
                    status.language: status.content,
                    },
                'attachment': status.media_attachments,
                'tag': status.tags,
                'replies': replies,
                }

class StatusActivitySerializer(serializers.ModelSerializer):

    class Meta:
        model = trilby_models.Status

    def to_representation(self, status):

        replies = [
                self.to_representation(x)
                for x in status.replies.all()]

        if status.reblog_of is None:
            type_field = 'Create'
            object_field = StatusObjectSerializer(status).data
        else:
            type_field = 'Announce'
            object_field = status.reblog_of.url

        return {
                'id': status.activity_url,
                'type': type_field,
                'actor': status.account.url,
                'published': status.created_at,
                'to': status.to,
                'cc': status.cc,
                'object': object_field,
               }

class ImageField(serializers.Field):

    def to_representation(self, value):
        return {
                'type': 'Image',
                'mediaType': 'image/jpeg', # FIXME always?
                'url': value,
                }

class PersonEndpointSerializer(serializers.BaseSerializer):

    def to_representation(self, instance):
        return {
                'sharedInbox': uri_to_url(
                    settings.KEPI['SHARED_INBOX_LINK'],
                    ),
                }

class PersonPublicKeySerializer(serializers.BaseSerializer):

    def to_representation(self, instance):
        return {
                'id': instance.url+'#main-key',
                'owner': instance.url,
                'publicKey': instance.publicKey,
                }

class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = trilby_models.LocalPerson
        fields = (
                'id',
                'type',
                'following',
                'followers',
                'inbox',
                'outbox',
                'featured',
                'endpoints',
                'preferredUsername',
                'name',
                'summary',
                'url',
                'manuallyApprovesFollowers',
                'publicKey',
                'tag',
                'attachment',
                'icon',
                'image',
                )

    id = serializers.URLField(
            source = "url",
            )

    type = ConstantField(
            value="Person",
            )

    following = serializers.URLField(
            source = "following_url",
            )

    followers = serializers.URLField(
            source = "followers_url",
            )

    inbox = serializers.URLField(
            source = "inbox_url",
            )

    outbox = serializers.URLField(
            source = "outbox_url",
            )

    featured = serializers.URLField(
            source = "featured_url",
            )

    endpoints = PersonEndpointSerializer(
            source = '*',
            )

    publicKey = PersonPublicKeySerializer(
            source = '*',
            )

    preferredUsername = serializers.CharField(
            source = "username",
            )

    name = serializers.CharField(
            source = "display_name",
            )

    summary = serializers.CharField(
            source = "note",
            )

    manuallyApprovesFollowers = serializers.BooleanField(
            source = "auto_follow",
            )

    tag = ConstantField(
            value = [],
            )

    attachment = ConstantField(
            value = [],
            )

    icon = ImageField(
            source='icon_or_default',
            )

    image = ImageField(
            source='header_or_default',
            )
