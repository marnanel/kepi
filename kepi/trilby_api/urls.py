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

    path('api/v1/accounts/<name>', User.as_view()),
    path('api/v1/accounts/<name>/statuses', Statuses.as_view()),
    path('api/v1/accounts/<name>/following', Following.as_view()),
    path('api/v1/accounts/<name>/followers', Followers.as_view()),
    path('api/v1/accounts/<name>/follow', Follow.as_view()),
    path('api/v1/accounts/<name>/unfollow', Unfollow.as_view()),

    path('api/v1/statuses', Statuses.as_view()),
    path('api/v1/statuses/<id>', Statuses.as_view()),
    path('api/v1/statuses/<id>/context', StatusContext.as_view()),

    # Favourite, aka like
    path('api/v1/statuses/<id>/favourite', Favourite.as_view()),
    path('api/v1/statuses/<id>/unfavourite', Unfavourite.as_view()),
    path('api/v1/statuses/<id>/favourited_by', StatusFavouritedBy.as_view()),

    # Reblog, aka boost
    path('api/v1/statuses/<id>/reblog', Reblog.as_view()),
    path('api/v1/statuses/<id>/unreblog', Unreblog.as_view()),
    path('api/v1/statuses/<id>/reblogged_by', StatusRebloggedBy.as_view()),

    path('api/v1/notifications', Notifications.as_view()),
    path('api/v1/filters', Filters.as_view()),
    path('api/v1/custom_emojis', Emojis.as_view()),
    path('api/v1/timelines/public', PublicTimeline.as_view()),
    path('api/v1/timelines/home', HomeTimeline.as_view()),

    path('api/v1/search', Search.as_view()),

    path('users/<username>/feed', UserFeed.as_view()),
    ]
