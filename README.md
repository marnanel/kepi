django-kepi
===========

This is a Django library for ActivitySub. It's still at an
early stage, and you shouldn't particularly expect anything
to work properly. Its primary purpose is as part of the
un_chapeau Mastodon server.

Not everything described herein has actually been implemented.

django_kepi.views.ActivityObjectResponse
----------------------------------------
This renders a Django object into ActivityStreams form.
It calls the object's activity_get() method in order to
serialise it. If that method throws TombstoneException,
a Tombstone will be generated instead, and the HTTP
result code will be set to 410 (Gone).

Collections
-----------
These are based on ordinary Django ordered querysets.
(Responses? Views?)

Each subclass must reimplement get_queryset() to return
the relevant queryset. It may also reimplement serialize_object(),
which will serialize objects found in the queryset. If
you don't reimplement serialize_object(), activity_get() will
be called on the object as usual.

Objects which throw TombstoneException will be represented
with Tombstones, but this won't affect the HTTP result code.

django_kepi.TombstoneException
------------------------------
If ActivityObjectResponse calls an object's activity_get() method to ask it
to render itself, and that method throws TombstoneException,
ActivityObjectResponse will produce an HTTP status of 410 (Gone)
and return a Tombstone object (as specified in ActivityPub).

If activity_get() is called during producing a Collection,
and throws TombstoneException, the object will be represented
by a Tombstone object, but the HTTP status code will be unaffected.

django_kepi.models.resolve()
----------------------------
Takes a URL identifier, and returns the object it refers to,
in this way:

First, we check django_kepi.models.NamedObject. If the URL is
listed there, we return the object referred to.

Secondly, if the hostname is one of the names of the current site,
we run the path through django.urls.resolve() to find the view function.

(XXX This won't work. NamedObject finds us an object, and
d.u.resolve() gets us a view function. They need to be the same.)

Lastly, XXX fallback.

django_kepi.models.QuarantinedMessage
-------------------------------------
An activity message we've received from another server, but
haven't had a chance to verify.

Kepi will dump all incoming messages here. Verification is
never done while processing a request.

XXX explain how we do this in batch mode

Both the body of the message and the HTTP headers must be signed,
otherwise the message is discarded.

XXX Do both signatures have to use the same key?

To verify a message, we need to know the details of:
 - the Actor who sent it, who must have nominated that key as
    their public key
 - the public key, which must name the Actor as its owner.

If a message fails verification, it gets logged and discarded.
If it passes verification, it gets created as a new
django_kepi.models.Activity.

django_kepi.models.NamedObject
------------------------------
....

django_kepi.models.Activity
---------------------------
...

