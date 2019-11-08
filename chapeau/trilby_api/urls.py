from django.urls import path
from .views import *

urlpatterns = [

    path('api/v1/instance', Instance.as_view()),
    path('api/v1/apps', Apps.as_view()),
    path('api/v1/accounts/verify_credentials', Verify_Credentials.as_view()),
    path('api/v1/accounts/<name>', User.as_view()),
    path('api/v1/accounts/<name>/statuses', Statuses.as_view()),

    path('api/v1/statuses', Statuses.as_view()),
    path('api/v1/statuses/<id>', Statuses.as_view()),
    path('api/v1/statuses/<id>/context', StatusContext.as_view()),
    path('api/v1/notifications', Notifications.as_view()),
    path('api/v1/filters', Filters.as_view()),
    path('api/v1/custom_emojis', Emojis.as_view()),
    path('api/v1/timelines/public', PublicTimeline.as_view()),
    path('api/v1/timelines/home', HomeTimeline.as_view()),

    path('users/<username>/feed', UserFeed.as_view()),
    ]
