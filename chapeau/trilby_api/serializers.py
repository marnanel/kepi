from rest_framework import serializers
from .models import TrilbyUser
from chapeau.kepi.models import AcItem
from chapeau.kepi.create import create
from oauth2_provider.models import Application

#########################################

class _VisibilityField(serializers.CharField):
    # Is there really no general enum field?
    def to_representation(self, obj):
        return Visibility[obj].value

    def to_internal_value(self, obj):
        try:
            return Visibility(obj).name
        except KeyError:
            raise serializers.ValidationError('invalid visibility')

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
        fields = ('id', 'url', 'uri',
                'account',
                'in_reply_to_id',
                'in_reply_to_account_id',
                'reblog',
                'status',
                'content',
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
                'application',
                'language',
                'pinned',
                'idempotency_key',
                )

    def create(self, validated_data):

        posted_by = self.context['request'].user
        validated_data['posted_by'] = posted_by

        result = create(value=validated_data)
        return result

    id = serializers.IntegerField(
            read_only = True)

    account = UserSerializer(
            source = 'posted_by',
            read_only = True)

    status = serializers.CharField(
            write_only = True,
            source = 'content')

    content = serializers.CharField(
            read_only = True)

    created_at = serializers.DateTimeField(
            read_only = True)

    in_reply_to_id = serializers.PrimaryKeyRelatedField(
            queryset=AcItem.objects.all,
            required = False)

    url = serializers.URLField(
            read_only = True)

    uri = serializers.URLField(
            read_only = True)

    # TODO Media

    sensitive = serializers.BooleanField(
            required = False)
    spoiler_text = serializers.CharField(
            required = False)

    visibility = _VisibilityField(
            required = False)

    def visibility_validation(self, value):
        if value not in Visibility:
            raise serializers.ValidationError('invalid visibility')

        return value

    idempotency_key = serializers.CharField(
            write_only = True,
            required = False)
