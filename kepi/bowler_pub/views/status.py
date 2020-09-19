# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import django.views
import logging
import kepi.bowler_pub.views.activitypub as ap
import kepi.trilby_api.models.status as status

logger = logging.getLogger(name='kepi')

class StatusView(ap.KepiView):
    def activity_get(self, request, *args, **kwargs):
        self._username = kwargs['username']
        self._status = kwargs['status']

        logger.debug("Looking up status %d, by %s",
                self._status, self._username,
                )

        try:
            result = status.Status.objects.get(
                    id = self._status,
                    )
        except status.Status.DoesNotExist:
            logger.info('  -- unknown status: %s', kwargs)
            return None

        logger.debug("  -- found %s",
                result
                )

        result = result.original

        logger.debug("  -- found %s",
                result
                )

        try:
            if result.account.username != self._username:
                logger.info('  -- status was by %s but they wanted %s',
                    result.account.username, self._username)
                return None
        except status.Status.account.RelatedObjectDoesNotExist:
            logger.warning("  -- status %d has no associated account "+\
                    "(shouldn't happen)",
                    self._status)
            return None

        return result
