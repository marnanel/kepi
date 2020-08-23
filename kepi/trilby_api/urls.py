# urls.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

from django.urls import path
from .views import *

urlpatterns = [

    path('api/v1/instance', Instance.as_view()),
    path('api/v1/instance/', Instance.as_view()), # keep tootstream happy
    path('api/v1/apps', Apps.as_view()),

    path('api/v1/accounts/verify_credentials', Verify_Credentials.as_view()),
    path('api/v1/accounts/update_credentials',
        UpdateCredentials.as_view()),

    path('api/v1/accounts/search', AccountsSearch.as_view()),

    path('api/v1/accounts/<user>', User.as_view()),
    path('api/v1/accounts/<user>/statuses', Statuses.as_view()),
    path('api/v1/accounts/<user>/following', Following.as_view()),
    path('api/v1/accounts/<user>/followers', Followers.as_view()),
    path('api/v1/accounts/<user>/follow', Follow.as_view()),
    path('api/v1/accounts/<user>/unfollow', Unfollow.as_view()),

    path('api/v1/statuses', Statuses.as_view()),
    path('api/v1/statuses/<status>', SpecificStatus.as_view()),
    path('api/v1/statuses/<status>/context', StatusContext.as_view()),

    # Favourite, aka like
    path('api/v1/statuses/<status>/favourite', Favourite.as_view()),
    path('api/v1/statuses/<status>/unfavourite', Unfavourite.as_view()),
    path('api/v1/statuses/<status>/favourited_by', StatusFavouritedBy.as_view()),

    # Reblog, aka boost
    path('api/v1/statuses/<status>/reblog', Reblog.as_view()),
    path('api/v1/statuses/<status>/unreblog', Unreblog.as_view()),
    path('api/v1/statuses/<status>/reblogged_by', StatusRebloggedBy.as_view()),

    path('api/v1/notifications', Notifications.as_view()),
    path('api/v1/filters', Filters.as_view()),
    path('api/v1/custom_emojis', Emojis.as_view()),
    path('api/v1/timelines/public', PublicTimeline.as_view()),
    path('api/v1/timelines/home', HomeTimeline.as_view()),

    path('api/v1/search', Search.as_view()),

    path('users/<username>/feed', UserFeed.as_view()),
    ]
