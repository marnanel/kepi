from django.urls import path
from django_kepi.views import *

urlpatterns = [
    path('obj/<id>', ActivityObjectView.as_view())
]

