# fetch.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
import requests
from urllib.parse import urlparse
from kepi.trilby_api.models import RemotePerson

logger = logging.Logger("kepi")

def _get_url_from_webfinger(user):

    url = f'https://{user.hostname}/.well-known/'+\
            f'webfinger?acct={user.acct}'

    response = requests.get(
            url,
            headers = {
                'Accept': 'application/activity+json',
                },
            )

    if response.status_code!=200:
        user.status = response.status_code
        user.save()
        raise ValueError("Unexpected status code from webfinger lookup")

    self_link = [x for x in response.json()['links']
        if x.get("type",'') == "application/activity+json"]

    if not self_link:
        raise ValueError("Webfinger has no activity information")

    user.url = self_link[0]['href']

def _fetch_user_inner(user):

    # XXX If local...

    if user.url is None and user.acct is not None:
        _get_url_from_webfinger(user)

    if user.url is None:
        raise ValueError("No URL given.")

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
        user.status = response.status_code
        user.save()
        raise ValueError("Unexpected status code from activity lookup")

    try:
        details = response.json()
    except ValueError:
        raise ValueError("Response was not JSON")

    if details['type'] not in ['Actor', 'Person']:
        raise ValueError(
                "Remote user was an unexpected type: "+details['type'])

    if details['id'] != user.url:
        raise ValueError(
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
            # ... created_at?
            # ... bot?
            ('movedTo', 'moved_to'),
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
                raise ValueError("Remote user gave us someone else's key")

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

def fetch_user(username):

    # FIXME What if the user is local?
    # FIXME What if the RemotePerson already exists?

    if '@' in username:
        result = RemotePerson(
                acct = username,
                )
    else:
        result = RemotePerson(
                url = username,
                )

    result.save()

    try:
        _fetch_user_inner(result)
    except ValueError as ve:
        logging.info("%s: %s",
                result.url,
                ve,
                )

        if result.status==0:
            result.status = 404
            result.save()

        # but don't re-raise the exception

    return result

def fetch_status(url):

    response = requests.get(
            status.url,
            headers = {
                'Accept': 'application/activity+json',
                },
            )

    if response.status_code!=200:
        logger.info("%s: unexpected status code from status lookup: %d",
                url, response.status_code,
                )
        return

    status = Status(
            remote_url = url,
            )

    status.save()

    return status
