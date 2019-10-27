from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
from .models import TrilbyUser
from chapeau.kepi.models import AcItem
from chapeau.kepi.create import create as kepi_create
from oauth2_provider.models import Application

#########################################

class UserSerializer(serializers.ModelSerializer):

    id = serializers.CharField(
            source='username',
            read_only = True)

    avatar = serializers.CharField()
    header = serializers.CharField()

    # for the moment, treat these as the same.
    # the spec doesn't actually explain the difference!
    avatar_static = serializers.CharField(
            source='avatar',
            )
    header_static = serializers.CharField(
            source='header',
            )

    following_count = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    statuses_count = serializers.SerializerMethodField()

    def get_following_count(self, obj):
        return obj.actor['following_count']

    def get_followers_count(self, obj):
        return obj.actor['followers_count']

    def get_statuses_count(self, obj):
        return obj.actor['statuses_count']

    class Meta:
        model = TrilbyUser
        fields = (
                'id',
                'username',
                'acct',
                'display_name',
                'locked',
                'avatar',
                'header',
                'created_at',
                'followers_count',
                'following_count',
                'statuses_count',
                'note',
                'url',
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

class UserSerializerWithSource(UserSerializer):

    class Meta:
        model = UserSerializer.Meta.model
        fields = UserSerializer.Meta.fields + (
            'source',
            )

    source = serializers.SerializerMethodField()

    def get_source(self, user):
        return {
                'privacy': user.default_visibility,
                'sensitive': user.default_sensitive,
                'note': user.note,
                'language': user.language,
                }

#########################################

class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcItem
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
                'application',
                'language',
                'pinned',
                'idempotency_key',
                )

    def create(self, validated_data):
        posted_by = CurrentUserDefault()
        validated_data['posted_by'] = posted_by
        validated_data['type'] = 'Note'

        result = kepi_create(
                value = validated_data,
                )

        return result

    id = serializers.CharField(
            source='number',
            required = False,
            read_only = True)

    uri = serializers.URLField(
            required = False,
            read_only = True)

    url = serializers.URLField(
            required = False,
            read_only = True)

    account = serializers.CharField(
            source = 'posted_by',
            required = False,
            read_only = True)

    in_reply_to_id = serializers.PrimaryKeyRelatedField(
            queryset=AcItem.objects.all,
            required = False)

    in_reply_to_account_id = serializers.PrimaryKeyRelatedField(
            queryset=AcItem.objects.all,
            required = False)

    reblog = serializers.URLField(
            required = False,
            read_only = True)

    # "content" is read-only for HTML;
    # "status" is write-only for text (or Markdown)
    content = serializers.CharField(
            source='html',
            required = False,
            read_only = True)

    status = serializers.CharField(
            source='content',
            required = False,
            write_only = True)

    created_at = serializers.DateTimeField(
            source='published',
            required = False,
            read_only = True)

   # TODO Media

    sensitive = serializers.BooleanField(
            required = False)
    spoiler_text = serializers.CharField(
            required = False)

    visibility = serializers.CharField(
            required = False)

    language = serializers.CharField(
            required = False)

    idempotency_key = serializers.CharField(
            write_only = True,
            required = False)

class StatusContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcItem
        fields = (
                'ancestors',
                'descendants',
                )

        ancestors = serializers.ListField(
                child = serializers.CharField(),
                read_only = True)

        descendants = serializers.ListField(
                child = serializers.CharField(),
                read_only = True)
