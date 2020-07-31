# webfinger.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
import requests
import kepi.sombrero_sendpub.models as sombrero_models

logger = logging.Logger("kepi")

def get_webfinger(username, hostname):

    result = sombrero_models.WebfingerUser(
            username = username,
            hostname = hostname,
            )

    url = f'https://{hostname}/.well-known/'+\
            f'webfinger?acct={username}'

    response = requests.get(
            url,
            headers = {
                'Accept': 'application/activity+json',
                },
            )

    result.status = response.status_code

    if response.status_code!=200:
        result.save()
        logger.info("Unexpected status code from webfinger lookup")
        return result

    self_link = [x for x in response.json()['links']
        if x.get("type",'') == "application/activity+json"]

    if not self_link:
        result.save()
        logger.info("Webfinger has no activity information")
        return result

    result.url = self_link[0]['href']
    result.save()

    return result
