from django.urls import path, re_path
import django_kepi.views

urlpatterns = [
        re_path('^(?P<id>[0-9a-z]{8})$', django_kepi.views.ThingView.as_view()),
        path('users', django_kepi.views.AllUsersView.as_view()),
        path('users/<str:name>', django_kepi.views.ThingView.as_view()),
        path('users/<str:name>/inbox', django_kepi.views.InboxView.as_view()),
        path('users/<str:name>/outbox', django_kepi.views.OutboxView.as_view()),
        path('users/<str:name>/followers', django_kepi.views.FollowersView.as_view()),
        path('users/<str:name>/following', django_kepi.views.FollowingView.as_view()),
        path('sharedInbox', django_kepi.views.InboxView.as_view()),
        ]

