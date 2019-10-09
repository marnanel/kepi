from django.contrib import admin
from django.urls import path, re_path, include
from django.conf.urls.static import static
import chapeau.kepi.urls
import chapeau.trilby_api.urls
from . import settings

urlpatterns = [
        path(r'admin/', admin.site.urls),
        # path('', chapeau.tophat_ui.views.FrontPageView.as_view()), # or something
        path(r'', include(chapeau.kepi.urls)),
        path(r'', include(chapeau.trilby_api.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
