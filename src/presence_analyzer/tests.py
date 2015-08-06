# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest

from presence_analyzer import main, utils
from presence_analyzer import views  # pylint: disable=unused-import


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)
TEST_DATA_MANGLED_W_HEADER_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data',
    'test_data_mangled_w_header.csv'
)
TEST_USERS_XML = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_users.xml'
)


# pylint: disable=maybe-no-member, too-many-public-methods
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        main.app.config.update({'USERS_XML': TEST_USERS_XML})
        utils.get_data.cache_duration = -1
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday')

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(
            data[0],
            {u'user_id': 10, u'name': u'Kowalski A.',
             u'avatar': u'http://example.com:80/api/images/users/10'})

    def test_mean_time_weekday(self):
        """
        Test mean time view.
        """
        resp = self.client.get('api/v1/mean_time_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 7)
        self.assertListEqual(
            [[day, interval] for day, interval in data if interval > 0],
            [[u'Tue', 30047], [u'Wed', 24465], [u'Thu', 23705]]
        )

        resp = self.client.get('api/v1/mean_time_weekday/9000')
        self.assertEqual(resp.status_code, 404)

    def test_presence_weekday(self):
        """
        Test presence weekday view.
        """
        resp = self.client.get('api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 7+1)
        self.assertListEqual(
            [[day, interval] for day, interval in data if interval > 0],
            [[u'Weekday', u'Presence (s)'], [u'Tue', 30047], [u'Wed', 24465],
             [u'Thu', 23705]]
        )

        resp = self.client.get('api/v1/presence_weekday/9000')
        self.assertEqual(resp.status_code, 404)

    def test_api_presence_start_end(self):
        """
        Test mean start-end listing.
        """
        resp = self.client.get('/api/v1/presence_start_end/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertLessEqual(len(data), 7)
        for row in data:
            self.assertEqual(len(row), 3)
            _, start, end = row
            self.assertLessEqual(start, end)
        self.assertListEqual(data, [[u'Tue', 34745, 64792],
                                    [u'Wed', 33592, 58057],
                                    [u'Thu', 38926, 62631]])

        resp = self.client.get('/api/v1/presence_start_end/9000')
        self.assertEqual(resp.status_code, 404)

    def test_templates(self):
        """
        Test templates renderers
        """

        for url in ('/presence_weekday', '/presence_start_end',
                    '/mean_time_weekday'):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.content_type.split(';')[0], 'text/html')


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        main.app.config.update({'USERS_XML': TEST_USERS_XML})
        utils.get_data.cache_duration = -1

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(
            data[10][sample_date]['start'],
            datetime.time(9, 39, 5)
        )

    def test_get_mangled_data(self):
        """
        Test parsing of mangled CSV file.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_MANGLED_W_HEADER_CSV})
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [11, ])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[11])
        self.assertItemsEqual(data[11][sample_date].keys(), ['start', 'end'])
        self.assertEqual(
            data[11][sample_date]['start'],
            datetime.time(9, 19, 50)
        )

    def test_get_user_data(self):
        """
        Test parsing of user XML file.
        """
        data = utils.get_user_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11, ])
        self.assertIn('name', data[11])
        self.assertEqual(data[11]['name'], u'Nowak B.')

    def test_cache(self):
        """
        Test caching.
        """

        @utils.cache()
        def func(b, c=10):
            func.a += 1
            return func.a+b+c
        func.a = 0

        self.assertEqual(func(-1), 10)
        self.assertEqual(func(-1), func(-1))
        self.assertEqual(func(-1), func(-1))
        func.cache_duration = -1
        self.assertEqual(func(-1), 11)
        self.assertEqual(func(0, 0), 3)

        @utils.cache(copy=True)
        def f(): return []
        f().append('test')
        self.assertListEqual(f(), [])


def suite():
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return base_suite


if __name__ == '__main__':
    unittest.main()
