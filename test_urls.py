from django.urls import path
from django_kepi.views import *

urlpatterns = [
    path('obj/<id>', ActivityObjectView.as_view()),
    path('user/<username>/followers/', FollowersView.as_view())
]

