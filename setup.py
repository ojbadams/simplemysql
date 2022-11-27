""" setup.py """
#!/usr/bin/env python

from setuptools import setup

setup(
	name="simplemysql",
	version="1.25",
	description="An ultra simple wrapper for Python MySQLdb with very basic functionality, \
				 forked from https://github.com/knadh/simplemysql",
	author="Kailash Nadh, Oli Adams",
	author_email="",
	url="https://github.com/ojbadams/simplemysql",
	packages=['simplemysql'],
	download_url="https://github.com/ojbadams/simplemysql",
	license="GPLv2",
	classifiers=[
		"Development Status :: 3 - Alpha",
		"Intended Audience :: Developers",
		"Programming Language :: Python",
		"Natural Language :: English",
		"License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
		"Programming Language :: Python :: 3.5",
		"Topic :: Software Development :: Libraries :: Python Modules",
		"Topic :: Database",
		"Topic :: Software Development :: Libraries"
	],
	install_requires=["mysqlclient"]
)
