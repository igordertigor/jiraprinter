#!/usr/bin/env python3
"""
Create password/username token to use as credentials
"""

import base64
import getpass


def main():
    username = input('Please enter your jira user name: ')
    password = getpass.getpass('Please enter your jira password: ')

    token = base64.b64encode(bytes('{}:{}'.
                                   format(username, password).encode('utf-8')))
    print(str(token, 'utf-8'))


if __name__ == "__main__":
    main()
