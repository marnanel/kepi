# collections.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name="kepi")

class ErsatzModel(object):

    @classmethod
    def remote_form(cls):
        # This exists for compatibility with the models
        # defined in trilby_api.
        return cls

    def save(self):
        pass

    def __init__(self,
            url):

        self.url = url
        self.status = 0

        self._iter_items = []
        self._next_page = None

    def update(self, found):
        """
        Update this object with information retrieved from
        the remote server.
        """
        pass

class _CollectionPage(ErsatzModel):

    def update(self, found):
        self.items = found.get('items', [])
        self.items.extend(found.get('orderedItems', []))

        self.next = found.get('next', None)

class Collection(ErsatzModel):

    """
    Used in ActivityPub to represent a collection of objects.
    It's not helpful to represent this as a Django model, because
    it can change so unpredictably from moment to moment.

    Collections can be iterated over.

    Some Collections are paged: in these cases
    the main object contains a pointer to a series of
    CollectionPages. We don't represent CollectionPages
    directly, but the iterator knows how to handle them.

    A Collection can be ordered or unordered. We treat these
    identically at present.

    The behaviour of Collections in general is defined at
    https://www.w3.org/TR/activitystreams-core/#paging ,
    and their use in ActivityPub is defined at
    https://www.w3.org/TR/activitypub/#collections .
    """

    def update(self, found):
        """
        Update this Collection with information retrieved from
        the remote server.
        """

        if found['type'] not in ['Collection', 'OrderedCollection']:
            raise ValueError("Type %s isn't a collection",
                    found['type'])

        if found['id']!=self.url:
            raise ValueError("id mismatch: wanted %s, got %s" % (
                self.url, found['id']))

        for fieldname in [
                'totalItems', 'first',
                'prev', 'next',
                ]:
            if fieldname in found:
                setattr(self, fieldname, found[fieldname])
            else:
                setattr(self, fieldname, None)

        self.items = found.get('items', [])
        self.items.extend(found.get('orderedItems', []))

        logger.debug("%s: updated with items: %s",
                self.url,
                self.items,
                )

    def __len__(self):

        if self.totalItems is None:
            raise ValueError("%s: totalItems wasn't supplied",
                    self.url)

        return self.totalItems

    def __iter__(self):

        try:
            self._iter_items = self.items.copy()
            self._next_page = self.first
            logger.debug("%s: iteration: begin with %s",
                    self.url, self._iter_items)

        except AttributeError:
            self._iter_items = None
            self._next_page = None
            logger.info("%s: iteration: no content loaded", self.url)

        return self

    def __next__(self):
        if self._iter_items:
            return self._iter_items.pop(0)

        if self._next_page is None:
            logger.debug("%s: iteration: finished!",
                    self.url)
            raise StopIteration

        logger.debug("%s: iteration: fetching %s...",
                self.url, self._next_page)

        import kepi.sombrero_sendpub.fetch as fetch

        next_bit = fetch.fetch(
                self._next_page,
                expected_type = _CollectionPage,
                )

        self._iter_items = next_bit.items
        self._next_page = next_bit.next

        logger.debug('  -- containing %s',
                self._iter_items)

        return self._iter_items.pop(0)
