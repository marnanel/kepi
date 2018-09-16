import requests
from requests_http_signature import HTTPSignatureAuth

saved_headers = {'HTTP_SIGNATURE': 'keyId="https://queer.party/users/marnanel#main-key",algorithm="rsa-sha256",headers="(request-target) user-agent host date accept-encoding digest content-type",signature="XGp7GgotKiWOjAZnCscq4/8ZtmjDP1oGM5Ud9Xt3wFsvyE/XuZvq+MfInEGu1PN6PkxWaE6BYEr4L3Id/kBOL5JFpJvXT9A5nkGx0vyACHw876QQerswq0HfHGt3bDqbPlzsVPDReFSxfYSyAh0VRFR7wDBveDV7xjw66KqxqF5tcwFS9jARwuSU2Cu5nsQ/xlkY8tIZ+9JsdX/rZoV7ZMzK+2kU3HH6Qmuy4TN2f0d8ko34B7nWwKZEzCArhakbep2ajpbyYbqQd0g/Ew12HRk3ZSl+CX2K9ZJnKQw3eKG2ivAaizK5C5uG0uzfGcMmI/KgzbV2USjeguVI+o+jFg=="', 'mod_wsgi.listener_host': '', 'mod_wsgi.request_handler': 'wsgi-script', 'mod_wsgi.path_info': '/users/fred/inbox', 'HTTP_HOST': 'unchapeau-dev.marnanel.org', 'HTTP_CONNECTION': 'close', 'mod_wsgi.application_group': 'unchapeau-dev.marnanel.org|', 'mod_wsgi.script_reloading': '1', 'mod_wsgi.callable_object': 'application', 'wsgi.multithread': True, 'wsgi.url_scheme': 'https', 'mod_wsgi.daemon_restarts': '0', 'SSL_TLS_SNI': 'unchapeau-dev.marnanel.org', 'SERVER_ADMIN': 'webmaster@localhost', 'PATH_INFO': '/users/fred/inbox', 'SERVER_SOFTWARE': 'Apache/2.4.25 (Debian)', 'mod_wsgi.handler_script': '', 'SCRIPT_NAME': '', 'SERVER_SIGNATURE': '<address>Apache/2.4.25 (Debian) Server at unchapeau-dev.marnanel.org Port 443</address>\n', 'wsgi.multiprocess': True, 'REQUEST_SCHEME': 'https', 'mod_wsgi.total_requests': 3, 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_DATE': 'Mon, 03 Sep 2018 19:26:07 GMT', 'wsgi.input_terminated': True, 'mod_wsgi.thread_requests': 1, 'SERVER_NAME': 'unchapeau-dev.marnanel.org', 'mod_wsgi.connection_id': 'r4FRg4QcX1E', 'HTTP_USER_AGENT': 'http.rb/3.2.0 (Mastodon/2.4.5; +https://queer.party/)', 'SERVER_PORT': '443', 'wsgi.version': (1, 0), 'HTTP_ACCEPT_ENCODING': 'gzip', 'PATH_TRANSLATED': '/home/marnanel/proj/un_chapeau/un_chapeau/wsgi.py/users/fred/inbox', 'SERVER_ADDR': '172.20.177.129', 'mod_wsgi.daemon_start': '1536002767374653', 'REMOTE_PORT': '12026', 'mod_wsgi.thread_id': 2, 'CONTENT_TYPE': 'application/activity+json; charset=utf-8', 'DOCUMENT_ROOT': '/var/www/html/uc-fail/', 'QUERY_STRING': '', 'CONTEXT_DOCUMENT_ROOT': '/var/www/html/uc-fail/', 'REQUEST_METHOD': 'POST', 'mod_wsgi.request_id': 'dcVSg4QcX1E', 'HTTP_DIGEST': 'SHA-256=w6LDahS+63b4VwYoWGdfBW1hO28A5lXwC0cNZLRd4hg=', 'mod_wsgi.script_start': '1536002767375121', 'mod_wsgi.daemon_connects': '1', 'SCRIPT_FILENAME': '/home/marnanel/proj/un_chapeau/un_chapeau/wsgi.py', 'mod_wsgi.queue_start': '1536002767374150', 'CONTENT_LENGTH': '1280', 'mod_wsgi.ignore_activity': '0', 'REMOTE_ADDR': '51.15.146.0', 'GATEWAY_INTERFACE': 'CGI/1.1', 'mod_wsgi.script_name': '', 'mod_wsgi.listener_port': '443', 'mod_wsgi.version': (4, 6, 4), 'mod_wsgi.process_group': 'un_chapeau_test', 'CONTEXT_PREFIX': '', 'apache.version': (2, 4, 25), 'REQUEST_URI': '/users/fred/inbox', 'wsgi.run_once': False, 'mod_wsgi.enable_sendfile': '0'} 

saved_body = {"@context":["https://www.w3.org/ns/activitystreams","https://w3id.org/security/v1",{"manuallyApprovesFollowers":"as:manuallyApprovesFollowers","sensitive":"as:sensitive","movedTo":"as:movedTo","Hashtag":"as:Hashtag","ostatus":"http://ostatus.org#","atomUri":"ostatus:atomUri","inReplyToAtomUri":"ostatus:inReplyToAtomUri","conversation":"ostatus:conversation","toot":"http://joinmastodon.org/ns#","Emoji":"toot:Emoji","focalPoint":{"@container":"@list","@id":"toot:focalPoint"},"featured":"toot:featured","schema":"http://schema.org#","PropertyValue":"schema:PropertyValue","value":"schema:value"}],"id":"https://queer.party/49ebb121-e105-492f-9140-6ea0dcfcfb8a","type":"Follow","actor":"https://queer.party/users/marnanel","object":"https://unchapeau-dev.marnanel.org/users/fred/user","signature":{"type":"RsaSignature2017","creator":"https://queer.party/users/marnanel#main-key","created":"2018-09-03T19:26:03Z","signatureValue":"eJepWWsHmd4qgtIvRq6bp0KcJZoi1UukyvrrxyrMKNkMOzy1MiwpKA1Se0KaswI9VeHtHpLsv0ueiAkUKrIu652iPBC8BVfeSUa4JGhqoYp/fNuSZM9X8Y9TnC9vT1Pl68kVpfqOBXxFqf7FRro8KUl8591DLJ93eXhtF9t2qoSh2m+vw3jrG/SnLKBsoboqNF02xs59ABVlF3Gy7fNXFBbjnupA5y3vrb6kDT8FAHTlccCfGASGiIPYjQ0AlvG6/vPQB65jZrL8km1EAAfX15G+ilInunMPEh9/D0DQ/OItb4mQL4inC1cUzIa4GZl8hv1BDDv49AgK+pW5SShZzw=="}}

def key_resolver(key_id, algorithm):
    return b"-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAr0urC5s1NwqMoArz5/Ln\nzS6/ICKNUkYlE8OxlVDJXIpfjNDFQtln/Qc2JM4yw8IKOyBwV6JFl78InKUHP6Dd\n55I8QcrsLa1BIUgu1yu7oJBMkDUXmsOKwvIkAJI5x0a/L/yHsD1jgqtSkrrD7SDt\nVSvYwiKnusi9oUNLHiaufhXv8/qpdkmcjjZrM4VbhYSgiobvzH5nR2JTBcM69uaG\nFUCrbhx5aHmZUf0vIxeKoJtfwNibFQ+OWil47bXjLcWJbw1X9SBRkjvwWm+1Ihpw\n0c8FeuViBSS15dXFSCxATaOLiFUYMl810ctcIhNn799F59ymgNVNS76Af3xJNWiM\nOQIDAQAB\n-----END PUBLIC KEY-----\n"

def process_header_name(s):
    if s.upper().startswith('HTTP_'):
        s = s[5:]
    return s.replace('_','-').lower()

class CaseInsensitiveDict(dict):
    def __setitem__(self, key, value):
        super().__setitem__(key.lower(), value)

    def __getitem__(self, key):
        return super().__getitem__(key.lower())

    def __contains__(self, key):
        return super().__contains__(key.lower())

headers = CaseInsensitiveDict([(process_header_name(f),v) for (f,v) in saved_headers.items()])


headers['Authorization'] = 'Signature '+headers['Signature']

request = requests.Request(
        method = "POST",
        url = "https://unchapeau-dev.marnanel.org/users/fred/inbox",
        headers = headers,
        json = saved_body,
        )

HTTPSignatureAuth.verify(request, key_resolver=key_resolver)



