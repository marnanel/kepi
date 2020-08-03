# test_fetch.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

from unittest import skip
from django.test import TestCase
from kepi.sombrero_sendpub.fetch import fetch_user
from kepi.trilby_api.models import RemotePerson
from . import suppress_thread_exceptions
import httpretty
import logging
import requests

logger = logging.Logger("kepi")

EXAMPLE_USER_URL = "https://example.org/users/wombat"
EXAMPLE_ATSTYLE = "wombat@example.org"

EXAMPLE_USER_RESULT = """{"@context":["https://www.w3.org/ns/activitystreams",
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
"name":"The Wombat",
"summary":"I like being a wombat.",
"url":"https://example.org/@wombat",
"manuallyApprovesFollowers":false,
"publicKey":{"id":"https://example.org/users/wombat#main-key",
"owner":"https://example.org/users/wombat",
"publicKeyPem":"-----BEGIN PUBLIC KEY-----\\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAqjX5AgZxDY0udxuZlBRo\\n6K+mA6XNfmEoscra/YUOZ0c8tnl122vPV5DOdOrm0jpah+GUn7CK43UOCXMLJe3D\\nIO7Q3w4TgNTGFjNERO1Dlh3Jgw/CbFBNbIb1QyFS0QjKBUcLKgPezGxklyk8U2+E\\nrSiP1xOlZZMlSTcMlR5c0LRdQQ0TJ9Lx8MbH66B9qM6HnYP+Z2nkm6SwBw9QOAlo\\nIiz1H6JkHX9CUa8ZzVQwp82LRWI25I/Szc+MDvTqdLu3lljyxcHlpxhs9/5hfxu9\\n9/CUdbPU6TqAkpXMtzcfaSKb7bzbYTtxzlzTnQX6EtLdpGjBp+kGLAt+XozlBeSy\\nbQIDAQAB\\n-----END PUBLIC KEY-----\\n"},
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

EXAMPLE_WEBFINGER_URL = 'https://example.org/.well-known/webfinger?acct='+EXAMPLE_ATSTYLE
EXAMPLE_WEBFINGER_RESULT = """{"subject":"acct:wombat@example.org",
"aliases":["https://example.org/@wombat",
"https://example.org/users/wombat"],
"links":[{"rel":"http://webfinger.net/rel/profile-page",
"type":"text/html",
"href":"https://example.org/@wombat"},
{"rel":"http://schemas.google.com/g/2010#updates-from",
"type":"application/atom+xml",
"href":"https://example.org/users/wombat.atom"},
{"rel":"self",
"type":"application/activity+json",
"href":"https://example.org/users/wombat"},
{"rel":"salmon",
"href":"https://example.org/api/salmon/15322"},
{"rel":"magic-public-key",
"href":"data:application/magic-public-key,RSA.qjX5AgZxDY0udxuZlBRo6K-mA6XNfmEoscra_YUOZ0c8tnl122vPV5DOdOrm0jpah-GUn7CK43UOCXMLJe3DIO7Q3w4TgNTGFjNERO1Dlh3Jgw_CbFBNbIb1QyFS0QjKBUcLKgPezGxklyk8U2-ErSiP1xOlZZMlSTcMlR5c0LRdQQ0TJ9Lx8MbH66B9qM6HnYP-Z2nkm6SwBw9QOAloIiz1H6JkHX9CUa8ZzVQwp82LRWI25I_Szc-MDvTqdLu3lljyxcHlpxhs9_5hfxu99_CUdbPU6TqAkpXMtzcfaSKb7bzbYTtxzlzTnQX6EtLdpGjBp-kGLAt-XozlBeSybQ==.AQAB"},
{"rel":"http://ostatus.org/schema/1.0/subscribe",
"template":"https://example.org/authorize_interaction?uri={uri}"}]}"""

EXAMPLE_WEBFINGER_RESULT_NO_USER = """{"subject":"acct:wombat@example.org",
"aliases":["https://example.org/@wombat",
"https://example.org/users/wombat"],
"links":[{"rel":"http://webfinger.net/rel/profile-page",
"type":"text/html",
"href":"https://example.org/@wombat"},
{"rel":"http://schemas.google.com/g/2010#updates-from",
"type":"application/atom+xml",
"href":"https://example.org/users/wombat.atom"},
{"rel":"salmon",
"href":"https://example.org/api/salmon/15322"},
{"rel":"magic-public-key",
"href":"data:application/magic-public-key,RSA.qjX5AgZxDY0udxuZlBRo6K-mA6XNfmEoscra_YUOZ0c8tnl122vPV5DOdOrm0jpah-GUn7CK43UOCXMLJe3DIO7Q3w4TgNTGFjNERO1Dlh3Jgw_CbFBNbIb1QyFS0QjKBUcLKgPezGxklyk8U2-ErSiP1xOlZZMlSTcMlR5c0LRdQQ0TJ9Lx8MbH66B9qM6HnYP-Z2nkm6SwBw9QOAloIiz1H6JkHX9CUa8ZzVQwp82LRWI25I_Szc-MDvTqdLu3lljyxcHlpxhs9_5hfxu99_CUdbPU6TqAkpXMtzcfaSKb7bzbYTtxzlzTnQX6EtLdpGjBp-kGLAt-XozlBeSybQ==.AQAB"},
{"rel":"http://ostatus.org/schema/1.0/subscribe",
"template":"https://example.org/authorize_interaction?uri={uri}"}]}"""

class TestFetchUser(TestCase):

    @httpretty.activate
    def test_fetch_user(self):
        httpretty.register_uri(
                'GET',
                EXAMPLE_USER_URL,
                status=200,
                headers = {
                        'Content-Type': 'application/activity+json',
                        },
                body = EXAMPLE_USER_RESULT,
                )

        user = fetch_user(EXAMPLE_USER_URL)

        self._asserts_for_example_user(user)

    @httpretty.activate
    def test_fetch_user_404(self):
        httpretty.register_uri(
                'GET',
                EXAMPLE_USER_URL,
                status=404,
                headers = {
                        'Content-Type': 'text/plain',
                        },
                body = 'nope',
                )

        user = fetch_user(EXAMPLE_USER_URL)

        self.assertEqual(
                user.status,
                404,
                )

    @httpretty.activate
    def test_fetch_user_410(self):
        httpretty.register_uri(
                'GET',
                EXAMPLE_USER_URL,
                status = 410,
                headers = {
                        'Content-Type': 'text/plain',
                        },
                body = 'not any more!',
                )

        user = fetch_user(EXAMPLE_USER_URL)

        self.assertEqual(
                user.status,
                410,
                )

    @httpretty.activate
    def test_fetch_user_timeout(self):

        def timeout(request, uri, headers):
            raise requests.Timeout()

        httpretty.register_uri(
                'GET',
                EXAMPLE_USER_URL,
                status = 200,
                headers = {
                        'Content-Type': 'text/plain',
                        },
                body = timeout,
                )

        with suppress_thread_exceptions():
            user = fetch_user(EXAMPLE_USER_URL)

        self.assertEqual(
                user.status,
                0,
                )

    @httpretty.activate
    def test_fetch_user_no_such_host(self):

        def no_such_host(request, uri, headers):
            raise requests.ConnectionError()

        httpretty.register_uri(
                'GET',
                EXAMPLE_USER_URL,
                status = 200,
                headers = {
                        'Content-Type': 'text/plain',
                        },
                body = no_such_host,
                )

        with suppress_thread_exceptions():
            user = fetch_user(EXAMPLE_USER_URL)

        self.assertEqual(
                user.status,
                0,
                )

    @httpretty.activate
    def test_fetch_known_user(self):

        existing = RemotePerson(
                url = EXAMPLE_USER_URL,
                )
        existing.save()

        found = {}
        def finding(request, uri, headers):
            found['found'] = True
            return EXAMPLE_USER_RESULT

        httpretty.register_uri(
                'GET',
                EXAMPLE_USER_URL,
                status = 200,
                headers = {
                        'Content-Type': 'application/activity+json',
                        },
                body = finding,
                )

        user = fetch_user(EXAMPLE_USER_URL)

        self.assertNotIn(
                'found',
                found,
                msg = "Known remote user wasn't re-fetched",
                )

    def _asserts_for_example_user(self, user):

        self.assertEqual(
                user.display_name,
                'The Wombat',
                )

        self.assertEqual(
            user.publicKey,
                "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAqjX5AgZxDY0udxuZlBRo\n6K+mA6XNfmEoscra/YUOZ0c8tnl122vPV5DOdOrm0jpah+GUn7CK43UOCXMLJe3D\nIO7Q3w4TgNTGFjNERO1Dlh3Jgw/CbFBNbIb1QyFS0QjKBUcLKgPezGxklyk8U2+E\nrSiP1xOlZZMlSTcMlR5c0LRdQQ0TJ9Lx8MbH66B9qM6HnYP+Z2nkm6SwBw9QOAlo\nIiz1H6JkHX9CUa8ZzVQwp82LRWI25I/Szc+MDvTqdLu3lljyxcHlpxhs9/5hfxu9\n9/CUdbPU6TqAkpXMtzcfaSKb7bzbYTtxzlzTnQX6EtLdpGjBp+kGLAt+XozlBeSy\nbQIDAQAB\n-----END PUBLIC KEY-----\n",
                )

        self.assertEqual(
                user.note,
                'I like being a wombat.',
                )

        self.assertEqual(
                user.locked,
                False,
                )

        self.assertEqual(
                user.url,
                EXAMPLE_USER_URL,
                )

        self.assertEqual(
                user.username,
                'wombat',
                )

        self.assertEqual(
                user.status,
                200,
                )

        self.assertEqual(
                user.inbox,
                'https://example.org/inbox',
                )

        self.assertEqual(
                user.acct,
                'wombat@example.org',
                )

        self.assertEqual(
                user.is_local,
                False,
                )

    @httpretty.activate
    def test_atstyle(self):

        httpretty.register_uri(
        'GET',
        EXAMPLE_USER_URL,
        status=200,
        headers = {
                'Content-Type': 'application/activity+json',
                },
        body = EXAMPLE_USER_RESULT,
        )

        httpretty.register_uri(
                'GET',
                EXAMPLE_WEBFINGER_URL,
                status=200,
                headers = {
                    'Content-Type': 'application/jrd+json',
                    },
                body = EXAMPLE_WEBFINGER_RESULT,
                )

        user = fetch_user(EXAMPLE_ATSTYLE)

        self._asserts_for_example_user(user)


    @httpretty.activate
    def test_atstyle_404(self):

        httpretty.register_uri(
                'GET',
                EXAMPLE_WEBFINGER_URL,
                status=404,
                headers = {
                    'Content-Type': 'text/plain',
                    },
                body = "never heard of them",
                )

        fetch_user(EXAMPLE_ATSTYLE)

        user = RemotePerson.objects.get(acct=EXAMPLE_ATSTYLE)

        self.assertEqual(
                user.status,
                404,
                )

    @httpretty.activate
    def test_atstyle_410(self):

        httpretty.register_uri(
                'GET',
                EXAMPLE_WEBFINGER_URL,
                status=410,
                headers = {
                    'Content-Type': 'text/plain',
                    },
                body = "never heard of them",
                )

        fetch_user(EXAMPLE_ATSTYLE)

        user = RemotePerson.objects.get(acct=EXAMPLE_ATSTYLE)

        self.assertEqual(
                user.status,
                410,
                )

    @httpretty.activate
    def test_atstyle_no_activity(self):

        httpretty.register_uri(
                'GET',
                EXAMPLE_WEBFINGER_URL,
                status=200,
                headers = {
                    'Content-Type': 'application/jrd+json',
                    },
                body = EXAMPLE_WEBFINGER_RESULT_NO_USER,
                )

        fetch_user(EXAMPLE_ATSTYLE)

        user = RemotePerson.objects.get(acct=EXAMPLE_ATSTYLE)

        self.assertEqual(
                user.status,
                0,
                )

class TestFetchStatus(TestCase):

    pass
