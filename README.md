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

django_kepi.models.resolve()
----------------------------
...

django_kepi.models.QuarantinedMessage
-------------------------------------
...


