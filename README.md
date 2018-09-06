django-kepi
===========

This is a Django library for ActivityPub. It's still at an
early stage, and you shouldn't particularly expect anything
to work properly. Its primary purpose is as part of the
un_chapeau Mastodon server.

At present we aren't supporting local clients posting to a
user's outbox, though we should eventually.

Not everything described herein has actually been implemented.

django_kepi.responses.ActivityObjectResponse
--------------------------------------------
This renders a Django object into ActivityStreams form.
It reads the object's activity property in order to
serialise it. If that property throws TombstoneException,
a Tombstone will be generated instead, and the HTTP
result code will be set to 410 (Gone).

Some of these objects, such as Likes, will belong to django_kepi.
Other kinds, such as Persons and Articles, will belong to other apps.

django_kepi.responses.CollectionResponse
----------------------------------------
These are based on ordinary Django ordered querysets.

Each subclass must reimplement get_queryset() to return
the relevant queryset. It may also reimplement serialize_object(),
which will serialize objects found in the queryset. If
you don't reimplement serialize_object(), the object's activity property
will be used as usual.

Objects which throw TombstoneException will be represented
with Tombstones, but this won't affect the HTTP result code.

django_kepi.TombstoneException
------------------------------
If ActivityObjectResponse reads an object's activity property,
and that property throws TombstoneException,
ActivityObjectResponse will produce an HTTP status of 410 (Gone)
and return a Tombstone object (as specified in ActivityPub).

If an activity property is read while producing a Collection,
and it throws TombstoneException, the object will be represented
by a Tombstone object, but the HTTP status code will be unaffected.

Throwing TombstoneException doesn't remove the object's record from
NamedObjects, because we'll still need to find the Tombstone when
someone asks for it.

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

XXX Fallback function to handle fetching, etc, per Activity type

XXX explain about how remote objects will have local proxy objects
XXX explain how these proxy objects should never be served

XXX There's actually four things we might want to do to an object:
XXX  Create: ID + fields -> new object (serialised)
XXX  Get: ID -> existing object (deserialised)
XXX  Update: ID + fields -> existing object (partially serialised)
XXX  Delete: ID -> no object (or Tombstone)

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
This table maps URL identifiers to Django objects,
using the contenttypes mechanism.
It also keeps track of the object's ActivityObject type.
It keeps a timestamp, so the record can fade from the cache
(but we don't actually do that at present).

Any object we know about on a remote server must be listed in
this table. Objects on this server *may* be listed
in this table; if they're not django_kepi.models.resolve()
can also find them through following the URL path.

django_kepi.models.Activity
---------------------------
All our own Activities, and all the remote Activities we know about,
are listed here. Each is identified by a UUID.

Saving an Activity to this table may have side-effects, based
on the Activity type. For example, saving a Follow activity
constitutes a Follow request.

Activities have a "valid" flag, because they can be undone
by subsequent Activities of type Undo.

django_kepi.views.ActivityView
------------------------------
A class view which displays a django_kepi.models.Activity,
given its UUID. Only our own Activities will be displayed.

django_kepi.views.CollectionView
--------------------------------
A view of a queryset, based on django_kepi.responses.CollectionResponse.

Outgoing Activities
-------------------
....
