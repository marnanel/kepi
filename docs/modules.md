# Modules

Like any Django system, kepi consists of a set of interacting modules.
(Django calls these "apps", confusingly.) In theory, it should be
possible to pull any of these modules out and use them in another project.

## trilby_api

Trilby implements [the Mastodon protocol](https://docs.joinmastodon.org/).
It also holds the microblogging data-- user details, statuses, and so on.

## bowler_pub

Bowler implements [the ActivityPub protocol](https://www.w3.org/TR/activitypub/).
It receives incoming messages from other servers, validates them, and acts upon them.
It's also responsible for fetching ActivityPub objects from other servers.

## sombrero_sendpub

Sombrero delivers messages to other ActivityPub servers.
As part of this, it handles webfinger lookup.

## tophat_ui

Tophat handles the web UI. At present, we don't have much of a web interface:
Tophat produces only the root page. Eventually it will produce HTML pages,
and possibly Atom feeds, for user pages (when these are requested by a
browser, via the `Accept` header).

It should also have a general web UI as an alternative to using a client program.
Given the fact that we implement the Mastodon protocol,
it's possible we can just merge in Mastodon's entire web UI.

## busby_1st

Busby handles incoming webfinger lookups, as well as the other `.well-known` services
such as `host-meta`.
