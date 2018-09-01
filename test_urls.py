from django.urls import path
from django_kepi.views import *
from things_for_testing.views import *

urlpatterns = [
    path('obj/<id>', ActivityObjectView.as_view()),
    path('thing-users', ThingUserCollection.as_view()),
    path('users/<name>/followers', ThingUserFollowersView.as_view()),
    path('users/<name>/following', ThingUserFollowingView.as_view()),
]

