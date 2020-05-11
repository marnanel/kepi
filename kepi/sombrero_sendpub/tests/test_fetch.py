# test_fetch.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

from unittest import skip
from django.test import TestCase
from kepi.sombrero_sendpub.fetch import fetch
from kepi.trilby_api.models import Person
import httpretty
import logging

logger = logging.Logger("kepi")

EXAMPLE_USER = """{"@context":["https://www.w3.org/ns/activitystreams",
"https://w3id.org/security/v1",
{"manuallyApprovesFollowers":"as:manuallyApprovesFollowers",
"sensitive":"as:sensitive",
"movedTo":{"@id":"as:movedTo",
"@type":"@id"},
"alsoKnownAs":{"@id":"as:alsoKnownAs",
"@type":"@id"},
"Hashtag":"as:Hashtag",
"ostatus":"http://ostatus.org#",
"atomUri":"ostatus:atomUri",
"inReplyToAtomUri":"ostatus:inReplyToAtomUri",
"conversation":"ostatus:conversation",
"toot":"http://joinmastodon.org/ns#",
"Emoji":"toot:Emoji",
"focalPoint":{"@container":"@list",
"@id":"toot:focalPoint"},
"featured":{"@id":"toot:featured",
"@type":"@id"},
"schema":"http://schema.org#",
"PropertyValue":"schema:PropertyValue",
"value":"schema:value"}],
"id":"https://example.org/users/wombat",
"type":"Person",
"following":"https://example.org/users/wombat/following",
"followers":"https://example.org/users/wombat/followers",
"inbox":"https://example.org/users/wombat/inbox",
"outbox":"https://example.org/users/wombat/outbox",
"featured":"https://example.org/users/wombat/collections/featured",
"preferredUsername":"wombat",
"name":"",
"summary":"Who would stoop to be fearless-- like a tree?",
"url":"https://example.org/@wombat",
"manuallyApprovesFollowers":false,
"publicKey":{"id":"https://example.org/users/wombat#main-key",
"owner":"https://example.org/users/wombat",
"publicKeyPem":"-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAqjX5AgZxDY0udxuZlBRo\n6K+mA6XNfmEoscra/YUOZ0c8tnl122vPV5DOdOrm0jpah+GUn7CK43UOCXMLJe3D\nIO7Q3w4TgNTGFjNERO1Dlh3Jgw/CbFBNbIb1QyFS0QjKBUcLKgPezGxklyk8U2+E\nrSiP1xOlZZMlSTcMlR5c0LRdQQ0TJ9Lx8MbH66B9qM6HnYP+Z2nkm6SwBw9QOAlo\nIiz1H6JkHX9CUa8ZzVQwp82LRWI25I/Szc+MDvTqdLu3lljyxcHlpxhs9/5hfxu9\n9/CUdbPU6TqAkpXMtzcfaSKb7bzbYTtxzlzTnQX6EtLdpGjBp+kGLAt+XozlBeSy\nbQIDAQAB\n-----END PUBLIC KEY-----\n"},
"tag":[],
"attachment":[],
"endpoints":{"sharedInbox":"https://example.org/inbox"},
"icon":{"type":"Image",
"mediaType":"image/png",
"url":"https://example.org/icon.png"},
"image":{"type":"Image",
"mediaType":"image/png",
"url":"https://example.org/header.png"}}
"""

class TestFetch(TestCase):

    def test_fetch(self):
        fetch("https://example.org/users/wombat")
