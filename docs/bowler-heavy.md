# bowler-heavy

*(This may require knowledge of [the structure of kepi's modules](modules.md).)*

In February 2020 I realised kepi had gone off-course. Bowler, the ActivityPub module,
was capable of handling *any* ActivityPub message. Trilby, the Mastodon module,
was merely an interface to Bowler.

That was fair enough, but kepi is supposed to be a microblogging platform, and
it wasn't trivial to turn the ActivityPub data into users and statuses.
In addition, it was rather slow.

I put all this into a branch called `bowler-heavy`, and set about turning the tables.
In the new branch, `trilby-heavy`, all microblogging data was held by Trilby,
and Bowler only handled as much of the ActivityPub protocol as was necessary
to run a microblogging platform. `trilby-heavy` was later merged into `main`.

It's possible that `bowler-heavy` could be of use to someone who wanted to
build a more general ActivityPub system. The branch remains, and you're
welcome to use it!

The current version of Bowler is derived from the version in `bowler-heavy`,
and some extraneous code remains.
