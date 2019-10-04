from django.contrib import admin
from django.urls import path, re_path, include
from django.conf.urls.static import static
import django_kepi.urls
import trilby_api.urls
from . import settings

urlpatterns = [
        path(r'admin/', admin.site.urls),
        # path('', kepi.views.FrontPageView.as_view()), # or something
        path(r'', include(django_kepi.urls)),
        path(r'', include(django_kepi.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
