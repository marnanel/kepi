# Installation

**This may be out of date. See [this thread by Dr. Quadragon about installation](https://mastodon.ml/@drq/104956749009106205).**

kepi is still pre-alpha software, so installation is still a
little fiddly at present.

If anything here doesn't work, [please raise an issue about it](https://gitlab.com/marnanel/kepi/issues/new).

## Dr. Quadragon's installation commands

 * python3 -m venv kepienv
 * apt-get install python3-venv
 * python3 -m venv kepienv
 * source kepienv/bin/activate
 * git clone https://gitlab.com/marnanel/kepi.git
 * apt-get install git
 * source kepienv/bin/activate
 * git clone https://gitlab.com/marnanel/kepi.git
 * cd kepi
 * pip install -r requirements.txt
 * quit
 * apt-get install build-essential python3-dev
 * source kepienv/bin/activate
 * cd kepi
 * pip install -r requirements.txt
 * python manage.py test

# Older installation instructions (to merge in)

## Set up a virtual environment

Start out by setting up a *virtual environment*-- in other words,
a sandbox so that you don't affect everything else on the machine.

```
python3 -m venv kepienv
```

If your system tells you that `python3` isn't available, try plain
`python`. Python 2 is going away soon, but the command names might
take a while to catch up.

Now you have your virtual environment set up, you can activate it
by typing

```
source kepienv/bin/activate
```

Your prompt should now have `(kepienv)` at the start.

## Grab kepi from gitlab

Now you're going to get hold of the kepi source code:

```
git clone https://gitlab.com/marnanel/kepi.git
```

When git has finished downloading the source, you will have a
new directory named `kepi`. So, go into it.

```
cd kepi
```

## Get the dependencies

Python's package manager `pip` should make this fairly straightforward.
All *you* have to do is type:

```
pip install -r requirements.txt
```

## Test kepi before you start using it

Now, before you start using kepi for real, make sure it works!

```
python manage.py test
```

This will run all the tests, which might take a few moments.
If everything passes, we can go on. If not,
as before,
[please raise an issue](https://gitlab.com/marnanel/kepi/issues/new).

## Set up the database

Set up an empty database by typing

```
python manage.py migrate
```

This will create a SQLite database called `kepi.sqlite3` in the `kepi` directory.
(You can use other database systems as well, but this is the default.)

**XXX This section is out of date. It used to use management commands,
but those don't exist any more because of [bowler-heavy](bowler-heavy.md).
It's difficult to explain what to do here: creating a superuser is necessary but will result
in an unmatched TrilbyUser. [Issue 18 has all the details](https://gitlab.com/marnanel/kepi/-/issues/18).**

And now you've posted your first status.

Unfortunately, nobody can see it, because you haven't yet set up the webserver.
So, let's go on to that.

## Set up the webserver

kepi interfaces with the webserver using a system called `gunicorn` (which is
short for "green unicorn"). You've already installed gunicorn along with the
other dependencies. So we can start it up:

```
gunicorn kepi.wsgi
```

gunicorn is now listening on port 8000 of your computer, which is the
default.

## Check it works

Now you can point a browser at
[http://localhost:8000/users/me](http://localhost:8000/users/me)
and you should see the JSON form of the user `@me` you created earlier.

## Going on from here

gunicorn itself isn't suitable for facing the public internet.
You'll need to put something like nginx in front of it.
This document should explain that, and it will at some point.

[Back](../README.md)

