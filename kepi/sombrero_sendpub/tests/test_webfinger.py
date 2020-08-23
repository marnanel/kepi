# test_webfinger.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

from unittest import skip
from django.test import TestCase
from kepi.sombrero_sendpub.webfinger import get_webfinger
from . import suppress_thread_exceptions
import httpretty

EXAMPLE_USERNAME = "wombat"
EXAMPLE_HOSTNAME = "example.org"
EXAMPLE_USER_URL = f"https://{EXAMPLE_HOSTNAME}/users/{EXAMPLE_USERNAME}"
EXAMPLE_ATSTYLE = f"{EXAMPLE_USERNAME}@{EXAMPLE_HOSTNAME}"

EXAMPLE_WEBFINGER_URL = \
        f'https://{EXAMPLE_HOSTNAME}/.well-known/webfinger?acct={EXAMPLE_ATSTYLE}'

EXAMPLE_WEBFINGER_RESULT = f"""{{"subject":"acct:{EXAMPLE_USERNAME}@{EXAMPLE_HOSTNAME}",
"aliases":["https://{EXAMPLE_HOSTNAME}/@{EXAMPLE_USERNAME}",
"https://{EXAMPLE_HOSTNAME}/users/{EXAMPLE_USERNAME}"],
"links":[{{"rel":"http://webfinger.net/rel/profile-page",
"type":"text/html",
"href":"https://{EXAMPLE_HOSTNAME}/@{EXAMPLE_USERNAME}"}},
{{"rel":"http://schemas.google.com/g/2010#updates-from",
"type":"application/atom+xml",
"href":"https://{EXAMPLE_HOSTNAME}/users/{EXAMPLE_USERNAME}.atom"}},
{{"rel":"self",
"type":"application/activity+json",
"href":"https://{EXAMPLE_HOSTNAME}/users/{EXAMPLE_USERNAME}"}},
{{"rel":"salmon",
"href":"https://{EXAMPLE_HOSTNAME}/api/salmon/15322"}},
{{"rel":"magic-public-key",
"href":"data:application/magic-public-key,RSA.qjX5AgZxDY0udxuZlBRo6K-mA6XNfmEoscra_YUOZ0c8tnl122vPV5DOdOrm0jpah-GUn7CK43UOCXMLJe3DIO7Q3w4TgNTGFjNERO1Dlh3Jgw_CbFBNbIb1QyFS0QjKBUcLKgPezGxklyk8U2-ErSiP1xOlZZMlSTcMlR5c0LRdQQ0TJ9Lx8MbH66B9qM6HnYP-Z2nkm6SwBw9QOAloIiz1H6JkHX9CUa8ZzVQwp82LRWI25I_Szc-MDvTqdLu3lljyxcHlpxhs9_5hfxu99_CUdbPU6TqAkpXMtzcfaSKb7bzbYTtxzlzTnQX6EtLdpGjBp-kGLAt-XozlBeSybQ==.AQAB"}},
{{"rel":"http://ostatus.org/schema/1.0/subscribe",
"template":"https://{EXAMPLE_HOSTNAME}/authorize_interaction?uri={{uri}}"}}]}}"""

EXAMPLE_WEBFINGER_RESULT_NO_USER = f"""{{"subject":"acct:{EXAMPLE_USERNAME}@{EXAMPLE_HOSTNAME}",
"aliases":["https://{EXAMPLE_HOSTNAME}/@{EXAMPLE_USERNAME}",
"https://{EXAMPLE_HOSTNAME}/users/{EXAMPLE_USERNAME}"],
"links":[{{"rel":"http://webfinger.net/rel/profile-page",
"type":"text/html",
"href":"https://{EXAMPLE_HOSTNAME}/@{EXAMPLE_USERNAME}"}},
{{"rel":"http://schemas.google.com/g/2010#updates-from",
"type":"application/atom+xml",
"href":"https://{EXAMPLE_HOSTNAME}/users/{EXAMPLE_USERNAME}.atom"}},
{{"rel":"salmon",
"href":"https://{EXAMPLE_HOSTNAME}/api/salmon/15322"}},
{{"rel":"magic-public-key",
"href":"data:application/magic-public-key,RSA.qjX5AgZxDY0udxuZlBRo6K-mA6XNfmEoscra_YUOZ0c8tnl122vPV5DOdOrm0jpah-GUn7CK43UOCXMLJe3DIO7Q3w4TgNTGFjNERO1Dlh3Jgw_CbFBNbIb1QyFS0QjKBUcLKgPezGxklyk8U2-ErSiP1xOlZZMlSTcMlR5c0LRdQQ0TJ9Lx8MbH66B9qM6HnYP-Z2nkm6SwBw9QOAloIiz1H6JkHX9CUa8ZzVQwp82LRWI25I_Szc-MDvTqdLu3lljyxcHlpxhs9_5hfxu99_CUdbPU6TqAkpXMtzcfaSKb7bzbYTtxzlzTnQX6EtLdpGjBp-kGLAt-XozlBeSybQ==.AQAB"}},
{{"rel":"http://ostatus.org/schema/1.0/subscribe",
"template":"https://{EXAMPLE_HOSTNAME}/authorize_interaction?uri={{uri}}"}}]}}"""

class TestWebfinger(TestCase):

    @httpretty.activate
    def test_simple(self):

        httpretty.register_uri(
                'GET',
                EXAMPLE_WEBFINGER_URL,
                status=200,
                headers = {
                    'Content-Type': 'application/jrd+json',
                    },
                body = EXAMPLE_WEBFINGER_RESULT,
                )

        webfinger = get_webfinger(
                EXAMPLE_USERNAME,
                EXAMPLE_HOSTNAME,
                )

        self.assertEqual(
                webfinger.url,
                EXAMPLE_USER_URL,
                )

    @httpretty.activate
    def test_404(self):

        httpretty.register_uri(
                'GET',
                EXAMPLE_WEBFINGER_URL,
                status=404,
                headers = {
                    'Content-Type': 'text/plain',
                    },
                body = "never heard of them",
                )

        webfinger = get_webfinger(
                EXAMPLE_USERNAME,
                EXAMPLE_HOSTNAME,
                )

        self.assertEqual(
                webfinger.url,
                None,
                )

    @httpretty.activate
    def test_410(self):

        httpretty.register_uri(
                'GET',
                EXAMPLE_WEBFINGER_URL,
                status=410,
                headers = {
                    'Content-Type': 'text/plain',
                    },
                body = "this bird has flown",
                )

        webfinger = get_webfinger(
                EXAMPLE_USERNAME,
                EXAMPLE_HOSTNAME,
                )

        self.assertEqual(
                webfinger.url,
                None,
                )

    @httpretty.activate
    def test_no_user(self):

        httpretty.register_uri(
                'GET',
                EXAMPLE_WEBFINGER_URL,
                status=200,
                headers = {
                    'Content-Type': 'application/jrd+json',
                    },
                body = EXAMPLE_WEBFINGER_RESULT_NO_USER,
                )

        webfinger = get_webfinger(
                EXAMPLE_USERNAME,
                EXAMPLE_HOSTNAME,
                )

        self.assertEqual(
                webfinger.url,
                None,
                )

    @httpretty.activate
    def test_timeout(self):

        def timeout(request, uri, headers):
            raise requests.Timeout()

        httpretty.register_uri(
                'GET',
                EXAMPLE_WEBFINGER_URL,
                status=200,
                headers = {
                    'Content-Type': 'application/jrd+json',
                    },
                body = timeout,
                )

        with suppress_thread_exceptions():
            webfinger = get_webfinger(
                    EXAMPLE_USERNAME,
                    EXAMPLE_HOSTNAME,
                    )

        self.assertEqual(
                webfinger.url,
                None,
                )

    @httpretty.activate
    def test_no_such_host(self):

        def no_such_host(request, uri, headers):
            raise requests.ConnectionError()

        httpretty.register_uri(
                'GET',
                EXAMPLE_WEBFINGER_URL,
                status=200,
                headers = {
                    'Content-Type': 'application/jrd+json',
                    },
                body = no_such_host,
                )

        with suppress_thread_exceptions():
            webfinger = get_webfinger(
                    EXAMPLE_USERNAME,
                    EXAMPLE_HOSTNAME,
                    )

        self.assertEqual(
                webfinger.url,
                None,
                )
