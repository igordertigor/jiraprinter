#!/usr/bin/env python3

import shlex

import requests
import markdown
from jinja2 import Template
import re
import os
import begin
import logging
import bottle
from urllib.parse import urlencode

logging.getLogger("requests").setLevel(logging.WARNING)

DEFAULT_TEMPLATE = os.path.join(os.path.dirname(__file__), 'html', 'template.html')


class Jira(object):

    def __init__(self, b64user, url):
        self.url = url
        self.auth = b64user
        self.__headers = None
        self.epic_id_field = 'customfield_14531'  # Don't know why but it's always there

    @property
    def headers(self):
        if self.__headers is None:
            self.__headers = {
                'Authorization': 'Basic {}'.format(self.auth),
                'Content-Type': 'application/json',
            }
        return self.__headers


class JiraPrinter(Jira):

    def __init__(self, b64user, url, template):
        super(JiraPrinter, self).__init__(b64user, url)
        self.template = template

    def process(self, ticket_ids):
        tickets = [self.get_processed_issue(ticket_id) for ticket_id in ticket_ids]
        return self.template.render(issues=tickets)

    def get_processed_issue(self, ticket_id):
        logging.info('Processing issue %s', ticket_id)
        ticket = self.get_raw_issue(ticket_id)
        ticket['description'] = self.description2html(ticket['description'])
        ticket['ticket_id'] = ticket_id
        epic = self.get_epic_name(ticket)
        if epic:
            ticket['epic'] = epic
        return ticket

    def get_raw_issue(self, ticket_id):
        response = requests.get(self.url + '/issue/{}'.format(ticket_id),
                                headers=self.headers)
        if response.ok:
            return response.json()['fields']
        raise requests.exceptions.HTTPError('{} (Error code={})'.format(response.content, response.status_code))

    def description2html(self, description):
        if description is None:
            return ''
        for i in range(2, 7):
            description = re.sub(r'h{}. '.format(i),
                                 r'#'*i + ' ',
                                 description)
        description = re.sub(r'^(\*\s)', r'- ', description, re.MULTILINE)
        description = re.sub(r'^(\+\s)', r'- ', description, re.MULTILINE)
        return markdown.markdown(description)

    def get_epic_name(self, ticket):
        epic_id = ticket[self.epic_id_field]
        try:
            epic_issue = self.get_raw_issue(epic_id)
        except requests.exceptions.HTTPError:
            return None  # Seems like there is no epic here
        return epic_issue


class JiraSearcher(Jira):

    def __init__(self, b64user, url):
        super(JiraSearcher, self).__init__(b64user, url)

    def search(self, params):
        data = self.get_raw_query(params)
        issues = data['issues']
        info = []
        for issue in issues:
            fields = issue['fields']
            info.append({'key': issue['key'],
                         'summary': fields['summary'],
                         'team': 'unknown',
                         'epic': fields[self.epic_id_field]
                         })
        return info

    def get_raw_query(self, params):
        query = self.assemble_query_string(params)
        logging.info('Using query string %s', query)
        response = requests.get(self.url + '/search?jql=' + query,
                                headers=self.headers)
        if response.ok:
            return response.json()
        raise requests.exceptions.HTTPError('{} (Error code={})'.format(response.content, response.status_code))

    def assemble_query_string(self, params):
        return urlencode({key: '"{}"'.format(value) if ' ' in value else value for key, value in params.items()})


def show_fields(ticket_description):
    for field, value in ticket_description.items():
        print(field, ': ', value)


printer_app = bottle.Bottle()

@printer_app.route('/')
def selection_display():
    with open('html/selection_display.html', 'r') as f:
        return Template(f.read()).render()


@printer_app.route('/columns/')
def get_columns():
    query = bottle.request.query['query']
    query = dict(q.split("=") for q in shlex.split(query))
    jira_searcher = JiraSearcher(CREDENTIALS, URL)
    info = jira_searcher.search(query)
    logging.info('Found {} tickets'.format(len(info)))
    return {'tickets': info}


@printer_app.route('/printable', method='POST')
def printable():
    """Export a list of jira tickets to html"""
    template_name = bottle.request.forms.get('template')
    with open(template_name if len(template_name) else DEFAULT_TEMPLATE, 'r') as f:
        template = Template(f.read())

    tickets = dict(bottle.request.forms)
    del tickets['template']
    del tickets['query']
    ticket_ids = [ticket for ticket in tickets]
    jira_printer = JiraPrinter(CREDENTIALS, URL, template)
    return jira_printer.process(ticket_ids)


@printer_app.route('/template', method='GET')
def printer_template():
    with open(DEFAULT_TEMPLATE, 'r') as f:
        return f.read()


@begin.subcommand()
def select():
    """Select tickets to print from a web interface"""
    bottle.run(printer_app, host='localhost', port="8080")


@begin.subcommand()
def export(outputfile: 'Name of output html file' ='tickets.html',
           template: 'Name of jinja2 template' =DEFAULT_TEMPLATE,
           *ticket_ids: 'Ids of tickets to convert'
           ):
    """Export a list of jira tickets to html"""
    with open(template, 'r') as f:
        template = Template(f.read())

    jira_printer = JiraPrinter(CREDENTIALS, URL, template)

    with open(outputfile, 'w') as f:
        f.write(
            jira_printer.process(ticket_ids)
        )


@begin.start(env_prefix='JIRA')
@begin.logging
def main(url: 'Url of the jira api',
         credentials: 'should contain username:password in base64 encoding'
         ):
    global URL
    global CREDENTIALS
    URL = url
    CREDENTIALS = credentials
