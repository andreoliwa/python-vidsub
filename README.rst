========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |appveyor| |requires|
        | |coveralls|
        | |codeclimate|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/python-videodrome/badge/?style=flat
    :target: https://readthedocs.org/projects/python-videodrome
    :alt: Documentation Status

.. |travis| image:: https://api.travis-ci.org/andreoliwa/python-videodrome.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/andreoliwa/python-videodrome

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/andreoliwa/python-videodrome?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/andreoliwa/python-videodrome

.. |requires| image:: https://requires.io/github/andreoliwa/python-videodrome/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/andreoliwa/python-videodrome/requirements/?branch=master

.. |coveralls| image:: https://coveralls.io/repos/andreoliwa/python-videodrome/badge.svg?branch=master&service=github
    :alt: Coverage Status
    :target: https://coveralls.io/r/andreoliwa/python-videodrome

.. |codeclimate| image:: https://codeclimate.com/github/andreoliwa/python-videodrome/badges/gpa.svg
   :target: https://codeclimate.com/github/andreoliwa/python-videodrome
   :alt: CodeClimate Quality Status

.. |version| image:: https://img.shields.io/pypi/v/videodrome.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/videodrome

.. |wheel| image:: https://img.shields.io/pypi/wheel/videodrome.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/videodrome

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/videodrome.svg
    :alt: Supported versions
    :target: https://pypi.org/project/videodrome

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/videodrome.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/videodrome

.. |commits-since| image:: https://img.shields.io/github/commits-since/andreoliwa/python-videodrome/v0.0.0.svg
    :alt: Commits since latest release
    :target: https://github.com/andreoliwa/python-videodrome/compare/v0.0.0...master



.. end-badges

Tools to sync subtitles and fix video file names

* Free software: MIT license

Installation
============

::

    pip install videodrome

You can also install the in-development version with::

    pip install https://github.com/andreoliwa/python-videodrome/archive/master.zip


Documentation
=============


https://python-videodrome.readthedocs.io/


Development
===========

To run all the tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
