import django.views
from django.shortcuts import render
import logging

logger = logging.Logger('django_kepi')

class HostMeta(django.views.View):

    def get(self, request):

        logger.info('Returning host-meta.xml')

        context = {
                'hostname': request.get_host(),
            }

        result = render(
                request=request,
                template_name='host-meta.xml',
                context=context,
                content_type='application/xrd+xml',
                )

        return result

