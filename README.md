# jira ticket printer

Jira does not provide a nice printable layout for tickets and nicer printing
options are costly. This script just wraps the jira-api to allow formatting
using jinja2 templates. This way, tickets can easily be formatted in a printer
friendly way.

## Getting started

Set up a virtual environment

    $ mkvirtualenv jiraprinter

and install the requirements into that virtual environment

    $ workon jiraprinter
    $ pip install -r requirements.txt

You can run the command line tool by calling

    python jira.py export <Ticket-Id> [<Ticket-Id> ...]

Here, angle brackets (`<>`) denote variable parameters and square brackets (`[]`) denote optional
parameters. This is similar to unix `man` pages. You can start the web-interface for selecting
tickets and printing them by calling

    $ python jira.py select

The web-interface will then be available at `localhost:8080`.

## Setting your credentials

It is recommended that you put the URL of your jira server as well as your
credentials into separate environment variables. Your user credentials need to
be passed in base 64 encoding, which can be done using the `prepare_token.py` script:

    $ ./prepare_token.py
    Please enter your jira user name: myname
    Please enter your jira password:
    fowkeofoakjdfolai

That last name is your jira credentials in base 64 encoding. It is recommended
that you set your jira credentials and the url of the server in your bashrc (if
you use bash). To do so, add the following lines to your `~/.bashrc` file.

    export JIRAURL=https://jira.mycompany/rest/api/2
    export JIRACREDENTIALS=fowkeofoakjdfolai

Obviously, both the URL and the credentials are completely made up.

## Authentication error

Error messages are typically rather long and complex. If you see a 401 status code somewhere at the end of the stacktrace, that means that you're not correctly authenticated. In that case, you might want to check your user name and password.
