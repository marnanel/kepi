django-kepi
===========

kepi is a Django library for ActivityPub, using Python 3.
It's still at an early stage, and you shouldn't particularly expect anything
to work properly.

Help is always appreciated.

Purpose
-------

This project has two purposes:

 * a Django library for ActivityPub. This is the ```django_kepi``` app.

 * a standalone daemon for other local programs to interact with.
   This is the ```kepi``` project (in the Django sense).

Running it
----------

Nothing out of the ordinary. Create your virtual environment:

```
$ python3 -m venv wombat
$ wombat/bin/activate
```

If ```python3``` doesn't work, try plain ```python```.

Then go wherever you put the kepi sources, and run the installation:

```
$ pip -r requirements.txt
$ python manage.py tests
$ python manage.py runserver
```

then check whether you can see anything at [https://127.0.0.1:8000/admin/](https://127.0.0.1:8000/admin/) .

Please don't make kepi's server visible beyond your local network. It's not designed to serve the general internet.
If you're installing for more than just testing, use nginx or apache to proxy requests.

History
-------

kepi started life as part of [the un_chapeau project](https://gitlab.com/marnanel/un_chapeau).
un_chapeau is a Mastodon-like system written with Django in Python.
kepi was split off from this, because it seemed more generally useful.

(All the subsystems of un_chapeau are named after kinds of hat;
a kepi is a kind of hat worn by French gendarmes.)

