from unittest import TestCase
from kepi.tophat_ui.view_for_mimetype import view_for_mimetype
class Tests(TestCase):

    def test_for_mimetype(self):

        vfm = view_for_mimetype(
                [
                    ('text', 'html', lambda req: 'th'),
                    ('application', 'json', lambda req: 'aj'),
                    ],
                default = lambda req: 'df',
                )

        class DummyRequest:
            def __init__(self, accept):
                self.headers = {
                        'Accept': accept,
                        }

        self.assertEqual(
                vfm(DummyRequest('text/html')),
                'th',
                )

        self.assertEqual(
                vfm(DummyRequest('application/json')),
                'aj',
                )

        self.assertEqual(
                vfm(DummyRequest(
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,*/*;q=0.8,application/json",
                    )),
                'th',
                )

        self.assertEqual(
                vfm(DummyRequest(
                    "application/xhtml+xml,"
                    "application/xml;q=0.9,*/*;q=0.8,application/json,"
                    "text/html",
                    )),
                'aj',
                )

        self.assertEqual(
                vfm(DummyRequest('image/jpg')),
                'df',
                )

        self.assertEqual(
                vfm(DummyRequest('')),
                'df',
                )

        vfm_no_default = view_for_mimetype(
                [
                    ('text', 'html', lambda req: 'th'),
                    ('application', 'json', lambda req: 'aj'),
                    ],
                )

        self.assertEqual(
                vfm_no_default(DummyRequest('text/html')),
                'th',
                )

        # But unknown requests get an HttpResponse object
        # with status_code==406.

        self.assertEqual(
                vfm_no_default(DummyRequest('image/jpeg')).status_code,
                406,
                )

        self.assertEqual(
                vfm_no_default(DummyRequest('')).status_code,
                406,
                )
