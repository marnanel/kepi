# trilby_api/views/__init__.py
#
# Part of kepi.
# Copyright (c) 2018-2021 Marnanel Thurman.
# Licensed under the GNU Public License v2.

from .other import \
        Instance, \
        Emojis, \
        Filters, \
        Search, \
        AccountsSearch

from .statuses import \
        Favourite, Unfavourite, \
        Reblog, Unreblog, \
        SpecificStatus, \
        Statuses, \
        StatusContext, \
        StatusFavouritedBy, \
        StatusRebloggedBy, \
        Notifications

from .persons import \
        Follow, Unfollow, \
        UpdateCredentials, \
        VerifyCredentials,\
        User, \
        Followers, Following

from .oauth import \
        Apps, \
        fix_oauth2_redirects

from .timelines import \
        PublicTimeline, \
        HomeTimeline, \
        UserFeed

__all__ = [
        # other
        'Instance',
        'Emojis',
        'Filters',
        'Search',
        'AccountsSearch',

        # statuses
        'Favourite', 'Unfavourite',
        'Reblog', 'Unreblog',
        'SpecificStatus',
        'Statuses',
        'StatusContext',
        'StatusFavouritedBy',
        'StatusRebloggedBy',
        'Notifications',

        # persons
        'Follow', 'Unfollow',
        'UpdateCredentials',
        'VerifyCredentials',
        'User',
        'Followers', 'Following',
        
        # oauth
        'Apps',
        'fix_oauth2_redirects',

        # timelines
        'PublicTimeline',
        'HomeTimeline',
        'UserFeed',
        ]
