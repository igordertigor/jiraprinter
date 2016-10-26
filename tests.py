import unittest
from unittest import mock

from collections import namedtuple
from jinja2 import Template
import requests

import jira

MockResponse = namedtuple('MockResponse', ['ok', 'json', 'content', 'status_code'])


class MockGet(object):
    def __init__(self, responses):
        self.responses = responses
        self.urls = []

    def __call__(self, url, **kwargs):
        self.urls.append(url)
        response = self.responses.pop(0)
        if response is None:
            raise requests.exceptions.HTTPError
        return response


class TestJiraBase(unittest.TestCase):

    def setUp(self):
        self.jira_object = jira.Jira('ldfkjals', 'https://jira.mycompany/rest/api/2')

    def test_headers_have_correct_keys(self):
        self.assertIn('Authorization', self.jira_object.headers)
        self.assertIn('Content-Type', self.jira_object.headers)


class TestJiraPrinter(unittest.TestCase):

    def setUp(self):
        with open('html/template.html', 'r') as f:
            self.jira_object = jira.JiraPrinter(
                'ldfkjals', 'https://jira.mycompany/rest/api/2',
                Template(f.read()))

    def test_process_results_in_template_that_contains_ticket_id(self):
        ticket_fields = {'ticket_id': 'TICKET-1234',
                         'summary': 'some summary',
                         'description': '',
                         'customfield_14531': ''}
        mock_get = MockGet([
            MockResponse(True, lambda: {'fields': ticket_fields}, '', 200),
            MockResponse(False, None, 'some content', 404),
        ])

        with mock.patch('jira.requests.get', mock_get):
            rendered = self.jira_object.process(['TICKET-1234'])

        self.assertIn('TICKET-1234', rendered)

    def test_process_calls_get_with_correct_url(self):
        ticket_fields = {'ticket_id': 'TICKET-1234',
                         'summary': 'some summary',
                         'description': '',
                         'customfield_14531': 'TICKET-0000'}
        epic_fields = {'ticket_id': 'TICKET-0000',
                       'summary': 'epic summary',
                       'description': '',
                       'customfield_14531': ''}
        mock_get = MockGet([
            MockResponse(True, lambda: {'fields': ticket_fields}, '', 200),
            MockResponse(True, lambda: {'fields': epic_fields}, '', 200),
        ])

        with mock.patch('jira.requests.get', mock_get):
            self.jira_object.process(['TICKET-1234'])

        # We call the API twice: First for the ticket, then for the epic
        self.assertEqual(len(mock_get.urls), 2)
        self.assertIn('TICKET-1234', mock_get.urls[0])
        self.assertIn('TICKET-0000', mock_get.urls[1])

    def test_process_with_multiple_tickets_includes_all(self):
        ticket1_fields = {'ticket_id': 'TICKET-1',
                          'summary': '', 'description': '', 'customfield_14531': ''}
        ticket2_fields = {'ticket_id': 'TICKET-2',
                          'summary': '', 'description': '', 'customfield_14531': ''}
        mock_get = MockGet([
            MockResponse(True, lambda: {'fields': ticket1_fields}, '', 200),
            MockResponse(False, None, '', 404),
            MockResponse(True, lambda: {'fields': ticket2_fields}, '', 200),
            MockResponse(False, None, '', 404),
        ])

        with mock.patch('jira.requests.get', mock_get):
            output = self.jira_object.process(['TICKET-1', 'TICKET-2'])

        self.assertIn('TICKET-1', output)
        self.assertIn('TICKET-2', output)

    def test_get_raw_issue_with_ok_response_returns_fields(self):
        mock_get = MockGet([MockResponse(True, lambda: {'fields': 'ok'}, '', 200)])

        with mock.patch('jira.requests.get', mock_get):
            self.assertEqual(self.jira_object.get_raw_issue('ticket_id'), 'ok')

    def test_get_raw_issue_with_non_ok_response_raises_error(self):
        mock_get = MockGet([MockResponse(False, '', 'ExpectedError', 404)])
        with mock.patch('jira.requests.get', mock_get):
            self.assertRaises(requests.exceptions.HTTPError, lambda: self.jira_object.get_raw_issue('ticket_id'))


class TestJiraSearcher(unittest.TestCase):

    def setUp(self):
        self.jira_object = jira.JiraSearcher('ldfalk', '')

    def mock_raw_issues(self, *args, **kwargs):
        dummy_component = [{'name': 'test'}]
        return {'issues': [
            {'fields': {'summary': '', 'components': dummy_component, 'customfield_14531': ''}, 'key': 'ticket1'},
            {'fields': {'summary': '', 'components': dummy_component, 'customfield_14531': ''}, 'key': 'ticket2'},
            {'fields': {'summary': '', 'components': dummy_component, 'customfield_14531': ''}, 'key': 'ticket3'},
        ]}

    def test_assemble_query_with_single_parameter(self):
        query = self.jira_object.assemble_query_string({'component': 'mycomponent'})
        self.assertEqual(query, 'component=mycomponent&maxResults=100')

    def test_assemble_query_with_two_parameters(self):
        query = self.jira_object.assemble_query_string({'component': 'mycomponent', 'project': 'myproject'})
        self.assertIn(query, ['component=mycomponent&project=myproject&maxResults=100',
                              'project=myproject&component=mycomponent&maxResults=100'])

    def test_assemble_query_with_specified_maxResults(self):
        query = self.jira_object.assemble_query_string({'component': 'mycomponent', 'maxResults': 2})
        self.assertEqual(query, 'component=mycomponent&maxResults=2')

    def test_search_returns_all_issues(self):
        with mock.patch('jira.JiraSearcher.get_raw_query', self.mock_raw_issues):
            issues = self.jira_object.search({})
        self.assertEqual(len(issues), 3)

    def test_search_reassembles_issues_to_flat_format(self):
        with mock.patch('jira.JiraSearcher.get_raw_query', self.mock_raw_issues):
            issues = self.jira_object.search({})
        for issue in issues:
            self.assertIn('key', issue.keys())
            self.assertIn('summary', issue.keys())
            self.assertIn('team', issue.keys())
            self.assertIn('epic', issue.keys())
