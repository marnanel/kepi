Kepi's models
=============

Kepi uses [django-polymorphic](https://django-polymorphic.readthedocs.io/en/stable/) models
to represent ActivityPub messages.

The superclass is ``Object``. It has some important subclasses:
 * ``Activity`` is the superclass of all activities, such as ``Create`` and ``Like``.
 * ``Actor`` is the superclass of all actors, such as ``Person``.
 * ``Item`` is the superclass of Notes and so on. (These don't have
   a superclass other than ``Object`` in the spec, so ``Item`` is a name
   you'll only see here.)

``Object`` used to be called ``Thing``, in case people confused it
with Python's own ``object`` class. But now it's ``Object`` with a
capital O. You will still find some references to it as "thing", though.

``Object``s represent ActivityPub types, which are dicts. Therefore,
``Object``s have fields. The fields may be stored in various ways:
 * As a field of the ``Object`` itself, prefixed with ``f_``. The prefix
    allows us to have fields such as ``type``, which is a Python
    reserved word.
 * In a ``ThingField`` which refers to the ``Object``. The values of a
    ``ThingField`` are stored as JSON, so they can be arbitrary.
 * Anything else the ``Object`` makes up, as long as it can provide
    it to accessors.

``Object`` fields may be read and written via subscripting (e.g.
``foo['type']``. You may append flags to the argument
separated by double underscores. I will document these flags
at some point.

All ``Object``s have an ``activity_form`` property which
returns their representation as a dict.
