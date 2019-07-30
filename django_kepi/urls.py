from django.urls import path, re_path
import django_kepi.views

urlpatterns = [
        re_path('^(?P<id>[0-9a-z]{8})$', django_kepi.views.ThingView.as_view()),
        path('users', django_kepi.views.AllUsersView.as_view()),
        path('users/<str:username>', django_kepi.views.ActorView.as_view()),
        path('users/<str:username>/inbox', django_kepi.views.InboxView.as_view(),
            { 'listname': 'inbox', } ),
        path('users/<str:username>/outbox', django_kepi.views.OutboxView.as_view(),
            { 'listname': 'outbox', } ),
        path('users/<str:username>/followers', django_kepi.views.FollowersView.as_view()),
        path('users/<str:username>/following', django_kepi.views.FollowingView.as_view()),
        path('sharedInbox', django_kepi.views.InboxView.as_view()),
        ]

