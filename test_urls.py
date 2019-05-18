from django.urls import path, include
import django_kepi.urls

urlpatterns = [
        path('', include(django_kepi.urls)),
]

