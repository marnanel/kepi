import kepi.trilby_api.signals as kepi_signals
from django.dispatch import receiver
from kepi.sombrero_sendpub.delivery import deliver
import logging

logger = logging.Logger("kepi")

@receiver(kepi_signals.followed)
def on_follow(sender, **kwargs):
    """
    If the Follow event describes a remote person being followed,
    then send them an ActivityPub "Follow" activity message about it.

    The spec for "Follow" is here:
    https://www.w3.org/TR/activitystreams-vocabulary/#dfn-follow
    """
    if sender.following.is_local:
        logger.debug("%s is local; not sending update", sender)
        return

    print("Follow received:", sender)
    logger.info("Follow received: %s", sender)

    deliver(
            activity = {
                'type': 'Follow',
                'actor': sender.follower.url,
                'object': sender.following.url,
                'to': sender.following.url,
                },
            )
