from main import *
import unittest


class FakeInternet:

    def __init__(self, url_and_text):
        self.url_and_text = url_and_text

    def get(self, url):
        if url.address not in self.url_and_text:
            return None
        return Response(url, self.url_and_text[url.address])


class FakeFS:
    def __init__(self):
        self.catalog = dict()

    def save(self, path, content):
        self.catalog[path] = content


class TestCalculator(unittest.TestCase):

    def test_recursive_references(self):
        internet = FakeInternet({
            "http://example.org/": '<a href="foo">this is a link</a>',
            "http://example.org/foo/": '<a href="/">this is a link</a>'
        })
        fs = FakeFS()

        app = App(internet, fs, 1e9, set())
        cur_depth = 0

        app.download(cur_depth, "http://example.org")

        self.assertEqual(fs.catalog, {
            "example.org/index.html": '<a href="foo/index.html">this is a link</a>',
            "example.org/foo/index.html": '<a href="../index.html">this is a link</a>'
        })

    def test_already_visited_url(self):
        internet = FakeInternet({
            "http://example.org/": '<a href="foo">this is a link</a>',
            "http://example.org/foo/": '<a href="/">this is a link</a>'
        })
        fs = FakeFS()

        app = App(internet, fs, 1, set())
        cur_depth = 0

        app.download(cur_depth, "http://example.org")

        self.assertEqual(fs.catalog, {
            "example.org/index.html": '<a href="foo/index.html">this is a link</a>',
            "example.org/foo/index.html": '<a href="../index.html">this is a link</a>'
        })

    def test_depth_is_null(self):
        internet = FakeInternet({
            "http://example.org/": '<a href="foo">this is a link</a>',
            "http://example.org/foo/": '<a href="bar">this is a link</a>',
            "http://example.org/foo/bar/": '<a href="baz">this is a link</a>',
            "http://example.org/foo/bar/baz/": 'Hi!'
        })
        fs = FakeFS()

        app = App(internet, fs, 0, set())
        cur_depth = 0

        app.download(cur_depth, "http://example.org")

        self.assertEqual(fs.catalog, {
            "example.org/index.html": '<a href="http://example.org/foo">this is a link</a>'
        })

    def test_depth_is_one(self):
        internet = FakeInternet({
            "http://example.org/": '<a href="foo">this is a link</a>',
            "http://example.org/foo/": '<a href="bar">this is a link</a>',
            "http://example.org/foo/bar/": '<a href="baz">this is a link</a>',
            "http://example.org/foo/bar/baz/": 'Hi!'
        })
        fs = FakeFS()

        app = App(internet, fs, 1, set())
        cur_depth = 0

        app.download(cur_depth, "http://example.org")

        self.assertEqual(fs.catalog, {
            "example.org/index.html": '<a href="foo/index.html">this is a link</a>',
            "example.org/foo/index.html": '<a href="http://example.org/foo/bar">this is a link</a>'
        })

    def test_depth_is_two(self):
        internet = FakeInternet({
            "http://example.org/": '<a href="foo">this is a link</a>',
            "http://example.org/foo/": '<a href="bar">this is a link</a>',
            "http://example.org/foo/bar/": '<a href="baz">this is a link</a>',
            "http://example.org/foo/bar/baz/": 'Hi!'
        })
        fs = FakeFS()

        app = App(internet, fs, 2, set())
        cur_depth = 0

        app.download(cur_depth, "http://example.org")

        self.assertEqual(fs.catalog, {
            "example.org/index.html": '<a href="foo/index.html">this is a link</a>',
            "example.org/foo/index.html": '<a href="bar/index.html">this is a link</a>',
            "example.org/foo/bar/index.html": '<a href="http://example.org/foo/bar/baz">this is a link</a>'
        })

    def test_depth_is_three(self):
        internet = FakeInternet({
            "http://example.org/": '<a href="foo">this is a link</a>',
            "http://example.org/foo/": '<a href="bar">this is a link</a>',
            "http://example.org/foo/bar/": '<a href="baz">this is a link</a>',
            "http://example.org/foo/bar/baz/": 'Hi!'
        })
        fs = FakeFS()

        app = App(internet, fs, 3, set())
        cur_depth = 0

        app.download(cur_depth, "http://example.org")

        self.assertEqual(fs.catalog, {
            "example.org/index.html": '<a href="foo/index.html">this is a link</a>',
            "example.org/foo/index.html": '<a href="bar/index.html">this is a link</a>',
            "example.org/foo/bar/index.html": '<a href="baz/index.html">this is a link</a>',
            "example.org/foo/bar/baz/index.html": 'Hi!'
        })

    def test_file_in_end(self):
        internet = FakeInternet({
            "http://example.org/index.html": '<a href="qux.html">this is a link</a>',
            "http://example.org/qux.html": 'Hi!'
        })
        fs = FakeFS()

        app = App(internet, fs, 2, set())
        cur_depth = 0

        app.download(cur_depth, "http://example.org/index.html")

        self.assertEqual(fs.catalog, {
                "example.org/index.html": '<a href="qux.html">this is a link</a>',
                "example.org/qux.html": 'Hi!',
                })

    def test_no_html_suffix(self):
        internet = FakeInternet({
            "http://example.org/":
                '<a href="foo">this is a link</a> <a href="/bar">this is a link</a>',
            "http://example.org/foo/": 'Hi!',
            "http://example.org/bar/": 'Bye!',
        })
        fs = FakeFS()
        app = App(internet, fs, 2, set())

        cur_depth = 0

        app.download(cur_depth, "http://example.org")

        self.assertEqual(fs.catalog, {
            "example.org/index.html":
                '<a href="foo/index.html">this is a link</a> <a href="bar/index.html">this is a link</a>',
            "example.org/foo/index.html": 'Hi!',
            "example.org/bar/index.html": 'Bye!',
                })

    def test_rel_root(self):
        internet = FakeInternet({
            "http://example.org/foo/bar/index.html": '<a href="/qux.html">this is a link</a>',
            "http://example.org/qux.html": 'Hi!',
        })
        fs = FakeFS()

        app = App(internet, fs, 2, set())
        cur_depth = 0

        app.download(cur_depth, "http://example.org/foo/bar/index.html")

        self.assertEqual(fs.catalog, {
                "example.org/foo/bar/index.html": '<a href="../../qux.html">this is a link</a>',
                "example.org/qux.html": 'Hi!',
                })

    def test_url_hard(self):
        url = Url("https://www.example.org/foo?q=123#bar")

        self.assertEqual(url.scheme, "https")
        self.assertEqual(url.domain, "www.example.org")
        self.assertEqual(url.path, 'www.example.org/foo/index.html')
