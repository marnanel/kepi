# middleware.py
#
# Part of kepi, an ActivityPub daemon.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
This is where we add the extra headers to outgoing responses.
All these headers go on everything we send out.
Some view-specific headers, like "Link", are added by the views instead.
"""

def add_headers(get_response):

    def middleware(request):

        response = get_response(request)

        response['X-Content-Type-Options'] = 'nosniff'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Vary'] = 'Accept, Accept-Encoding, Origin'
        response['Cache-Control'] = 'max-age=180, public'
        response['Transfer-Encoding'] = 'chunked'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        response['Referrer-Policy'] = 'no-referrer-when-downgrade'
        response['X-Frame-Options'] = 'DENY'

        return response

    return middleware
