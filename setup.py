#!/usr/bin/env python

from setuptools import setup


def read(fname):
    with open(fname) as f:
        return f.read()

setup(
    name='jiraprinter',
    author='Ingo Fruend',
    author_email='ingo.fruend@twentybn.com',
    description='Simple printing interface for jira',
    license='MIT',
    keywords='jira printing',
    py_modules=['jira'],
    long_description=read('README.md'),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only'
    ]
)
