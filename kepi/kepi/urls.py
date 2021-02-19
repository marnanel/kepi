from django.contrib import admin
from django.urls import path, re_path, include
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
import oauth2_provider.views as oauth2_views
import kepi.busby_1st.urls
import kepi.bowler_pub.urls
import kepi.trilby_api.urls
import kepi.tophat_ui.urls
from kepi.trilby_api.views import fix_oauth2_redirects
from . import settings

##################################
# OAuth2 provider endpoints

fix_oauth2_redirects()

oauth2_endpoint_views = [
    path(r'authorize/', oauth2_views.AuthorizationView.as_view(), name="authorize"),
    path(r'token/', oauth2_views.TokenView.as_view(), name="token"),
    path(r'revoke-token/', oauth2_views.RevokeTokenView.as_view(), name="revoke-token"),
]

oauth2_patterns = (oauth2_endpoint_views, "oauth2_provider")

##################################################

urlpatterns = [
        path(r'admin/', admin.site.urls),
        path(r'accounts/', include('django.contrib.auth.urls')),
        path(r'oauth2/', include(oauth2_patterns)),

        # kepi's own stuff
        path(r'', include(kepi.tophat_ui.urls)),
        path(r'', include(kepi.busby_1st.urls)),
        path(r'', include(kepi.bowler_pub.urls)),
        path(r'', include(kepi.trilby_api.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
