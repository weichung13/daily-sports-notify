import unittest
from datetime import date
from unittest.mock import patch
from urllib.error import HTTPError

from fotmob import normalize, validate_payload, format_schedule, fetch_day, fetch_schedule
from main import send_to_line

DAY = date(2026, 9, 16)


def match(identifier, utc, **status):
    return {'id': identifier, 'home': {'name': 'Home'}, 'away': {'name': 'Away'},
            'status': {'utcTime': utc, **status}}


def payload(matches, primary=133):
    return {'date': '20260916', 'leagues': [
        {'id': 938221, 'primaryId': primary, 'matches': matches}]}


class ScheduleTests(unittest.TestCase):
    def test_window_primary_id_and_duplicates(self):
        data = payload([
            match(1, '2026-09-15T15:59:00Z'),
            match(2, '2026-09-15T16:00:00Z'),
            match(3, '2026-09-16T20:00:00Z'),
            match(4, '2026-09-16T20:01:00Z')])
        result = normalize([data, data], DAY)
        self.assertEqual([m['id'] for m in result], ['2', '3'])
        self.assertEqual(result[0]['kickoff'].hour, 0)
        self.assertEqual(result[1]['kickoff'].hour, 4)
        self.assertEqual(result[0]['competition'], 'EFL Cup')

    def test_excluded_competition(self):
        self.assertEqual(normalize([payload([match(1, '2026-09-16T12:00:00Z')], 77)], DAY), [])

    def test_status_and_next_day_display(self):
        result = normalize([payload([match(1, '2026-09-16T19:00:00Z',
                                           reason={'short': 'PP', 'long': 'Postponed'})])], DAY)
        self.assertEqual(result[0]['status'], '延期')
        text = format_schedule(DAY, result)
        self.assertIn('09/17 03:00', text)
        self.assertIn('03:00 Home vs Away', text)

    def test_finished_matches_excluded_even_without_time(self):
        data = payload([match(1, None, finished=True),
                        match(2, '2026-09-16T12:00:00Z', started=True),
                        match(3, '2026-09-16T19:00:00Z', finished=False)])
        result = normalize([data], DAY)
        self.assertEqual([m['id'] for m in result], ['2', '3'])
        self.assertEqual(result[0]['status'], '進行中')
        self.assertNotIn('已結束', format_schedule(DAY, result))

    def test_grouping_keeps_both_dates_and_english_names(self):
        cup = payload([match(1, '2026-09-16T12:00:00Z'),
                       match(3, '2026-09-16T19:00:00Z')])
        league = payload([match(2, '2026-09-16T13:00:00Z')], 47)
        text = format_schedule(DAY, normalize([cup, league], DAY))
        self.assertEqual(text.count('【EFL Cup】'), 1)
        self.assertEqual(text.count('【Premier League】'), 1)
        self.assertLess(text.index('03:00 Home vs Away'), text.index('【Premier League】'))
        self.assertIn('09/16 20:00 Home vs Away', text)
        self.assertIn('09/17 03:00 Home vs Away', text)

    def test_all_finished_has_no_empty_competition_heading(self):
        result = normalize([payload([match(1, None, finished=True)])], DAY)
        text = format_schedule(DAY, result)
        self.assertIn('沒有尚未結束的比賽', text)
        self.assertNotIn('【EFL Cup】', text)

    def test_bad_or_missing_time_fails(self):
        for value in (None, 'invalid', '2026-09-16T12:00:00'):
            with self.assertRaises(ValueError):
                normalize([payload([match(1, value)])], DAY)

    def test_wrong_date_or_schema_fails(self):
        for data in ({}, {'date': '20260915', 'leagues': []}, {'date': '20260916', 'leagues': {}}):
            with self.assertRaises(ValueError):
                validate_payload(data, DAY)
        validate_payload({'date': '20260916', 'leagues': []}, DAY)

    @patch('fotmob.fetch_day')
    def test_fetches_both_local_dates(self, fetch):
        fetch.return_value = {'leagues': []}
        self.assertEqual(fetch_schedule(DAY), [])
        self.assertEqual([c.args[0] for c in fetch.call_args_list], [DAY, date(2026, 9, 17)])

    @patch('fotmob.urlopen')
    def test_forbidden_is_not_retried(self, request):
        request.side_effect = HTTPError('https://example.test', 403, 'Forbidden', {}, None)
        with self.assertRaises(HTTPError):
            fetch_day(DAY)
        self.assertEqual(request.call_count, 1)

    @patch.dict('os.environ', {'LINE_CHANNEL_ACCESS_TOKEN': 'test', 'LINE_USER_ID': 'test'})
    @patch('main.urlopen')
    def test_line_failure_propagates(self, request):
        request.side_effect = HTTPError('https://example.test', 401, 'Unauthorized', {}, None)
        with self.assertRaises(HTTPError):
            send_to_line('test')


if __name__ == '__main__':
    unittest.main()
