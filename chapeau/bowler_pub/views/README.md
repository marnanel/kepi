Kepi and views
==============

Django's ordinary views can receive requests for any of the HTTP methods:

 * GET
 * POST
 * HEAD...

KepiView is a subclass of Django's View, which can receive requests for two extra methods:

 * ACTIVITY_GET
 * ACTIVITY_STORE

These can't be received over the network. They allow local code to access local objects by their URL.

ACTIVITY_GET is far more common. It returns the actual object represented by the given URL.
For example, doing an ACTIVITY_GET on ``https://yourserver/users/alice`` would return the Actor
object representing Alice.

ACTIVITY_STORE passes another object to the object represented by the URL.
For example, passing a "Like" object to ``https://yourserver/users/alice/inbox`` would add
the "Like" to Alice's inbox.

bowler_pub.find() makes extensive use of the ACTIVITY methods.
