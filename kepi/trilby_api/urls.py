# urls.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

from django.urls import path
import kepi.trilby_api.views as views

urlpatterns = [

    path('api/v1/instance', views.Instance.as_view()),
    path('api/v1/instance/', views.Instance.as_view()), # keep tootstream happy
    path('api/v1/apps', views.Apps.as_view()),

    path('api/v1/accounts/verify_credentials', views.VerifyCredentials.as_view()),
    path('api/v1/accounts/update_credentials',
        views.UpdateCredentials.as_view()),

    path('api/v1/accounts/search', views.AccountsSearch.as_view()),

    path('api/v1/accounts/<user>', views.User.as_view()),
    path('api/v1/accounts/<user>/statuses', views.Statuses.as_view()),
    path('api/v1/accounts/<user>/following', views.Following.as_view()),
    path('api/v1/accounts/<user>/followers', views.Followers.as_view()),
    path('api/v1/accounts/<user>/follow', views.FollowUser.as_view()),
    path('api/v1/accounts/<user>/unfollow', views.UnfollowUser.as_view()),

    path('api/v1/statuses', views.Statuses.as_view()),
    path('api/v1/statuses/<status>', views.SpecificStatus.as_view()),
    path('api/v1/statuses/<status>/context', views.StatusContext.as_view()),

    # Favourite, aka like
    path('api/v1/statuses/<status>/favourite', views.Favourite.as_view()),
    path('api/v1/statuses/<status>/unfavourite', views.Unfavourite.as_view()),
    path('api/v1/statuses/<status>/favourited_by', views.StatusFavouritedBy.as_view()),

    # Reblog, aka boost
    path('api/v1/statuses/<status>/reblog', views.Reblog.as_view()),
    path('api/v1/statuses/<status>/unreblog', views.Unreblog.as_view()),
    path('api/v1/statuses/<status>/reblogged_by', views.StatusRebloggedBy.as_view()),

    path('api/v1/notifications', views.Notifications.as_view()),
    path('api/v1/filters', views.Filters.as_view()),
    path('api/v1/custom_emojis', views.Emojis.as_view()),
    path('api/v1/timelines/public', views.PublicTimeline.as_view()),
    path('api/v1/timelines/home', views.HomeTimeline.as_view()),

    path('api/v1/search', views.Search.as_view()),

    path('users/<username>/feed', views.UserFeed.as_view()),
    ]
