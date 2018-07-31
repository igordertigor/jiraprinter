#!/usr/bin/env python

from setuptools import setup, find_packages


def read(fname):
    try:
        import pypandoc
        return pypandoc.convert(fname, 'rst')
    except ImportError:
        with open(fname) as f:
            return f.read()

setup(
    name='jiraprinter',
    author='Ingo Fruend',
    author_email='ingo.fruend@twentybn.com',
    description='Simple printing interface for jira',
    version='0.0.1',
    license='MIT',
    keywords='jira printing',
    install_requires=['bottle', 'Jinja2', 'begins'],
    long_description=read('README.md'),
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'prepare_token.py   =   jiraprinter.prepare_token:main'
        ]
    },
    package_data={'jiraprinter': ['html/*.html']},
    include_package_data=True,
    scripts=['jiraprinter/jira.py'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only'
    ]
)
