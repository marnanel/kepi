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
        fields = (
                'id',
                'type',
                'summary',
                'inReplyTo',
                'published',
                'url',
                'attributedTo',
                'to',
                'cc',
                'sensitive',
                'content',
                'contentMap',
                'attachment',
                'tag',
                'replies',
                )

class CreateActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = trilby_models.Status
        fields = (
                'type',
                'actor',
                'published',
                'to',
                'cc',
                'object',
                )

    type = ConstantField(
            value="Create",
            )
    actor = serializers.CharField(
            source = "account",
            )
    published = serializers.DateTimeField(
            source = "created_at",
            )
    to = ConstantField(
            value="FIXME", # FIXME
            )
    cc = ConstantField(
            value="FIXME", # FIXME
            )
    object = ConstantField(
            value="FIXME", # FIXME
            )

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
