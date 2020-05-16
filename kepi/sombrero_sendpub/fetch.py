# test_fetch.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
import requests
from urllib.parse import urlparse
from celery import shared_task
from kepi.trilby_api.models import RemotePerson

logger = logging.Logger("kepi")

@shared_task()
def _async_fetch_user(user):

    def complain(complaint):
        logging.warn("%s: %s",
                user.url,
                complaint
                )

        user.status = 404
        user.save()

        raise ValueError(complaint)

    response = requests.get(
            user.url,
            headers = {
                'Accept': 'application/activity+json',
                },
            )

    user.status = response.status_code
    # FIXME What happens if the hostname doesn't exist,
    # FIXME or the named host doesn't run an https server?

    if response.status_code!=200:
        complain("Unexpected status code")

    try:
        details = response.json()
    except ValueError:
        complain("Response was not JSON")

    if details['type'] not in ['Actor', 'Person']:
        complain(
                "Remote user was an unexpected type: "+details['type'])

    if details['id'] != user.url:
        complain(
                "Remote user's id was not the source url: expected "+\
                        user.url+" but got "+details['id'])

    for detailsname, fieldname in [
            ('preferredUsername', 'username'),
            ('name', 'display_name'),
            ('summary', 'note'),
            ('manuallyApprovesFollowers', 'locked'),
            #('following', 'following'),
            #('followers', 'followers'),
            ('inbox', 'inbox'),
            #('outbox', 'outbox'),
            #('featured', 'featured'),
            # ... bot?
            # ... moved_to?
            ]:
        if detailsname in details:
            setattr(user,
                    fieldname,
                    details[detailsname])

    # A shared inbox takes priority over a personal inbox
    if 'endpoints' in details:
        if 'sharedInbox' in details['endpoints']:
            user.inbox = details['endpoints']['sharedInbox']

    if 'publicKey' in details:
        key = details['publicKey']

        if 'owner' in key:
            if key['owner'] != user.url:
                complain("Remote user gave us someone else's key")

        if 'id' in key:
            user.key_name = key['id']

        if 'publicKeyPem' in key:
            user.publicKey = key['publicKeyPem']

    if user.acct is None:

        # We might already know the acct,
        # if we got to this user by looking up their acct.
        # This will probably have to be cleverer later.

        hostname = urlparse(user.url).netloc
        user.acct = '{}@{}'.format(
            user.username,
            hostname,
            )

    # FIXME Header and icon

    user.save()

    return user

def fetch_user(url):

    result = RemotePerson(
            url = url,
            )
    result.save()

    _async_fetch_user(result)

    return result
