from rest_framework import serializers
from kepi.trilby_api.models.status import Status
from rest_framework_recursive.fields import RecursiveField

"""
These are the serialisers for ActivityPub.
"""

#########################################

temp_example = """
-VICTORIA_WOOD = {
-            "type": "Create",
-            "actor": "https://altair.example.com/users/alice",
-            "published": "2019-07-27T13:08:46Z",
-            "to": [
-                "https://www.w3.org/ns/activitystreams#Public"
-            ],
-            "cc": [
-                "https://altair.example.com/users/alice/followers"
-            ],
-            "object": {
-                "id": "https://altair.example.com/users/alice/statuses/102513569060504404",
-                "type": "Note",
-                "summary": None,
-                "inReplyTo": "https://altair.example.com/users/alice/statuses/102513505242530375",
-                "published": "2019-07-27T13:08:46Z",
-                "url": "https://altair.example.com/@marnanel/102513569060504404",
-                "attributedTo": "https://altair.example.com/users/alice",
-                "to": [
-                    "https://www.w3.org/ns/activitystreams#Public"
-                ],
-                "cc": [
-                    "https://altair.example.com/users/alice/followers"
-                ],
-                "sensitive": False,
-                "conversation": "tag:altair.example.com,2019-07-27:objectId=17498957:objectType=Conversation",
-                "content": "<p>Victoria Wood parodying Peter Skellern. I laughed so much at this, though you might have to know both singers&apos; work in order to find it quite as funny.</p><p>- love song<br />- self-doubt<br />- refs to northern England<br />- preamble<br />- piano solo<br />- brass band<br />- choir backing<br />- love is cosy<br />- heavy rhotic vowels</p><p><a href=\"https://youtu.be/782hqdmnq7g\" rel=\"nofollow noopener\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"\">youtu.be/782hqdmnq7g</span><span class=\"invisible\"></span></a></p>",
-                "contentMap": {
-                    "en": "<p>Victoria Wood parodying Peter Skellern. I laughed so much at this, though you might have to know both singers&apos; work in order to find it quite as funny.</p><p>- love song<br />- self-doubt<br />- refs to northern England<br />- preamble<br />- piano solo<br />- brass band<br />- choir backing<br />- love is cosy<br />- heavy rhotic vowels</p><p><a href=\"https://youtu.be/782hqdmnq7g\" rel=\"nofollow noopener\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"\">youtu.be/782hqdmnq7g</span><span class=\"invisible\"></span></a></p>",
-                },
-                "attachment": [],
-                "tag": [],
-                "replies": {
-                    "id": "https://altair.example.com/users/alice/statuses/102513569060504404/replies",
-                    "type": "Collection",
-                    "first": {
-                        "type": "CollectionPage",
-                        "partOf": "https://altair.example.com/users/alice/statuses/102513569060504404/replies",
-                        "items": []
-                    }
-                }
-            }
-}
"""

class StatusCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = (
                'type',
                'actor',
                'published',
                'to',
                'cc',
                'object',
                )

class StatusObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
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
