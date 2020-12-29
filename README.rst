My Tourist
==========

A free tool for analysis the potential audience of the region's tourism products.

.. image:: https://img.shields.io/badge/license-GPL%20v3-blue.svg
     :target: LICENSE
     :alt: License: GPL v3
.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
     :target: https://github.com/pre-commit/pre-commit
     :alt: Pre Commit: enabled
.. image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg
     :target: https://github.com/pydanny/cookiecutter-django/
     :alt: Built with Cookiecutter Django
.. image:: https://requires.io/github/eugena/my_tourist/requirements.svg?branch=master
     :target: https://requires.io/github/eugena/my_tourist/requirements/?branch=master
     :alt: Requirements Status
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
     :target: https://github.com/ambv/black
     :alt: Black code style


Settings
--------

Moved to settings_.

.. _settings: http://cookiecutter-django.readthedocs.io/en/latest/settings.html

Basic Commands
--------------

Setting Up Your Users
^^^^^^^^^^^^^^^^^^^^^

* To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

* To create an **superuser account**, use this command::

    $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

Type checks
^^^^^^^^^^^

Running type checks with mypy:

::

  $ mypy my_tourist

Test coverage
^^^^^^^^^^^^^

To run the tests, check your test coverage, and generate an HTML coverage report::

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

Running tests with py.test
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  $ pytest

Pre-commit
~~~~~~~~~~~~~~~~~~~~~~~~~~

Installation:
::

  $ pre-commit install


Checking project files:
::

  $ pre-commit run --all-files

Live reloading and Sass CSS compilation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Moved to `Live reloading and SASS compilation`_.

.. _`Live reloading and SASS compilation`: http://cookiecutter-django.readthedocs.io/en/latest/live-reloading-and-sass-compilation.html





Sentry
^^^^^^

Sentry is an error logging aggregator service. You can sign up for a free account at  https://sentry.io/signup/?code=cookiecutter  or download and host it yourself.
The system is setup with reasonable defaults, including 404 logging and integration with the WSGI application.

You must set the DSN url in production.


Deployment
----------

Supervisor
^^^^^^^^^^

Contents of the file /etc/supervisor/conf.d/my_tourist.conf:
::

    [program:my_tourist]
    command=docker-compose -f production.yml up
    directory=/var/www/my_tourist/
    redirect_stderr=true
    autostart=true
    autorestart=true
    priority=10


Manage:
::

    supervisorctl start my_tourist
    supervisorctl restart my_tourist
    supervisorctl stop my_tourist


Docker
^^^^^^

See detailed `cookiecutter-django Docker documentation`_.

.. _`cookiecutter-django Docker documentation`: http://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html


Maintenance
-----------

::

    docker-compose -f production.yml run -e MY_TOURIST_GLOBAL_CODE=XX --rm django python manage.py update_heat_map
