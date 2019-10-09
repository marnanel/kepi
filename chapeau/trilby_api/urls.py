from django.urls import path
from .views import *

urlpatterns = [

    path('api/v1/instance', Instance.as_view()),
    path('api/v1/apps', Apps.as_view()),
    path('api/v1/accounts/verify_credentials', Verify_Credentials.as_view()),
    path('api/v1/statuses', Statuses.as_view()),
    path('api/v1/timelines/public', PublicTimeline.as_view()),

    path('users/<username>/feed', UserFeed.as_view()),
    ]