# webfinger.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name="kepi")

import requests
import kepi.sombrero_sendpub.models as sombrero_models

def get_webfinger(username, hostname):

    result = sombrero_models.WebfingerUser(
            username = username,
            hostname = hostname,
            )

    url = f'https://{hostname}/.well-known/'+\
            f'webfinger?acct={username}'

    try:
        response = requests.get(
                url,
                headers = {
                    'Accept': 'application/activity+json',
                    },
                )
    except requests.ConnectionError:
        logger.info("webfinger: Connection to %s failed",
                hostname)
        result.status = 0
        result.save()
        return result

    result.status = response.status_code

    if response.status_code!=200:
        result.save()
        logger.info("webfinger: Unexpected status code %d from lookup of %s@%s",
                response.status_code,
                username, hostname)
        return result

    self_link = [x for x in response.json()['links']
        if x.get("type",'') == "application/activity+json"]

    if not self_link:
        result.save()
        logger.info("webfinger: retrieved %s@%s, which has no activity information",
                username, hostname)
        return result

    result.url = self_link[0]['href']
    result.save()

    return result
