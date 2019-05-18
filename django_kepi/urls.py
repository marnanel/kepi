from django.urls import path
from django_kepi.views import *

urlpatterns = [
        path('<uuid:id>', KepiView.as_view()),
        path('users/<str:name>', KepiView.as_view()),
        path('users/<str:name>/inbox', InboxView.as_view()),
        path('sharedInbox', InboxView.as_view()),
        ]

