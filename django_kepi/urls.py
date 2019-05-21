from django.urls import path
from django_kepi.views import *

urlpatterns = [
        path('<uuid:id>', ThingView.as_view()),
        path('users', AllUsersView.as_view()),
        path('users/<str:name>', ThingView.as_view()),
        path('users/<str:name>/inbox', InboxView.as_view()),
        path('users/<str:name>/followers', FollowersView.as_view()),
        path('users/<str:name>/following', FollowingView.as_view()),
        path('sharedInbox', InboxView.as_view()),
        ]

