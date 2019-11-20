from rest_framework import serializers
from kepi.bowler_pub.models import AcItem, AcActor
from kepi.bowler_pub.create import create as bowler_pub_create
from oauth2_provider.models import Application

#########################################

class UserSerializer(serializers.ModelSerializer):

    id = serializers.CharField(
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
            source='number',
            )

    display_name = serializers.CharField(
            source='f_name',
            )

    acct = serializers.CharField(
            source='number', # TODO: is it?
            )

    created_at = serializers.DateTimeField(
            source='published',
            )

    note = serializers.CharField(
            source='f_summary',
            )

    following_count = serializers.IntegerField()
    followers_count = serializers.IntegerField()
    statuses_count = serializers.IntegerField()

    class Meta:
        model = AcActor
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
                'note': user.f_summary,
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
        posted_by = self.context['request'].user
        validated_data['posted_by'] = posted_by
        validated_data['type'] = 'Note'

        result = bowler_pub_create(
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

    account = UserSerializer(
            source = 'actor',
            )

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
            allow_blank = True,
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
