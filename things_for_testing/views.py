from django.shortcuts import render
from django_kepi.views import *
from django_kepi.models import *
from things_for_testing.models import *

logger = logging.getLogger(name='things_for_testing')

class ThingUserView(KepiView):

    def activity(self, *args, **kwargs):
        logger.debug('ThingUserView.activity: %s', kwargs['name'])
        try:
            return ThingUser.objects.get(name=kwargs['name'])
        except ThingUser.DoesNotExist:
            logger.debug('  -- does not exist')
            return None

class ThingUserCollection(KepiView):
    def activity(self, *args, **kwargs):
        return ThingUser.objects.all()

    def _modify_list_item(self, obj):
        return obj.activity_form

class ThingUserFollowingView(KepiView):

    def activity(self, *args, **kwargs):
        return Activity.objects.filter(
                f_type='Follow',
                f_actor=ThingUser(name=kwargs['name']).activity_id,
                accepted=True,
                )

    def _modify_list_item(self, obj):
        return obj.f_object

class ThingUserFollowersView(KepiView):

    def activity(self, *args, **kwargs):
        return Activity.objects.filter(
                f_type='Follow',
                f_object=ThingUser(name=kwargs['name']).activity_id,
                accepted=True,
                )

    def _modify_list_item(self, obj):
        return obj.f_actor
