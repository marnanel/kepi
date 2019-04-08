from django.test import TestCase
from django_kepi.models import IncomingMessage, validate
from unittest.mock import patch
import django_kepi.validation

def _test_message():
    result = IncomingMessage(
            content_type = "application/activity+json",
            date = "Thu, 04 Apr 2019 21:12:11 GMT",
            digest = "SHA-256=MJRFYant/jJdSotCYRY4n1PtDFVIvYJxfCxydrimx/o=",
            host = "marnanel.org",
            signature = "keyId=\"https://queer.party/users/marnanel#main-key\",algorithm=\"rsa-sha256\",headers=\"(request-target) host date digest content-type\",signature=\"Db3Ua+VMRkfMc05p0r2te9pFHCOjAbtifagR7Q+Hjhc+VPsf5QNkPzMsIbSKuhZLRLkj3xDzbsiNrLg8zZOcM0MQCQGeL8ACgpBOm/nqB+USdUOcC7pdy1X/zN+oKbVroho3FgC53xHoEz3l7LVSTifzmhyf2/P8yFO7UpbcisX1fgazrjMhBPOI2Mv+JkDgBpBinzRS5V+O+RaJ9Hw8NjgI+1zvE/BHMLVttJYaI2vGt5ParqpVq3DLh5NeHuyXq6wRLI2ee5TxYAZiETpz3XKFpoOZOBi2P98mjTUAbFKyFc5C5/UfSgksy6fyuWtbmBouPXsKf1lEOmdC+dUt0Q==\"",
            body = "{\"@context\":[\"https://www.w3.org/ns/activitystreams\",\"https://w3id.org/security/v1\",{\"manuallyApprovesFollowers\":\"as:manuallyApprovesFollowers\",\"sensitive\":\"as:sensitive\",\"movedTo\":{\"@id\":\"as:movedTo\",\"@type\":\"@id\"},\"alsoKnownAs\":{\"@id\":\"as:alsoKnownAs\",\"@type\":\"@id\"},\"Hashtag\":\"as:Hashtag\",\"ostatus\":\"http://ostatus.org#\",\"atomUri\":\"ostatus:atomUri\",\"inReplyToAtomUri\":\"ostatus:inReplyToAtomUri\",\"conversation\":\"ostatus:conversation\",\"toot\":\"http://joinmastodon.org/ns#\",\"Emoji\":\"toot:Emoji\",\"focalPoint\":{\"@container\":\"@list\",\"@id\":\"toot:focalPoint\"},\"featured\":{\"@id\":\"toot:featured\",\"@type\":\"@id\"},\"schema\":\"http://schema.org#\",\"PropertyValue\":\"schema:PropertyValue\",\"value\":\"schema:value\"}],\"id\":\"https://queer.party/04b065f8-81c4-408e-bec3-9fb1f7c06408\",\"type\":\"Follow\",\"actor\":\"https://queer.party/users/marnanel\",\"object\":\"https://marnanel.org/users/marnanel\"}",
            actor = "https://queer.party/users/marnanel",
            key_id = "https://queer.party/users/marnanel#main-key",
                )
    return result

class TestValidation(TestCase):

    @patch('django_kepi.validation._kick_off_background_fetch')
    def test_local_lookup(self, mock_fetch):
        message = _test_message()
        validate(message)
        mock_fetch.assert_called_once_with('https://queer.party/users/marnanel')

