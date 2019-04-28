1) CachedPublicKey needs to become CachedRemoteUser.
   Add the user's inbox and outbox URLs to the model.

2) Can I easily create an Activity for creating a local Article?
   (Bear in mind that this instruction might have come in via the
    user's outbox, rather than locally.)

------

New challenge:
  Auto-send Accept responses for incoming follow requests.

------

Activities need to allow lists etc.
Can't we just store a JSON blob or something?

------

Delivery needs to be implemented.
What's the longest chain of lookups?

We'll probably need a Delivery model.

XXX This should all be done through Celery.
How good is Celery at task resumption even after a reboot?

------

Let's look at validation, done using Celery throughout.

We create an IncomingMessage, and save it, always.
Then we ask Celery to do the rest: validate_task.

One single function.
Based on CachedText; this does the fetch etc.

------

Is there something weird going on with our webfinger implementation?

-------

