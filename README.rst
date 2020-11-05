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
.. |docs| image:: https://readthedocs.org/projects/python-vidsub/badge/?style=flat
    :target: https://readthedocs.org/projects/python-vidsub
    :alt: Documentation Status

.. |travis| image:: https://api.travis-ci.org/andreoliwa/python-vidsub.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/andreoliwa/python-vidsub

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/andreoliwa/python-vidsub?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/andreoliwa/python-vidsub

.. |requires| image:: https://requires.io/github/andreoliwa/python-vidsub/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/andreoliwa/python-vidsub/requirements/?branch=master

.. |coveralls| image:: https://coveralls.io/repos/andreoliwa/python-vidsub/badge.svg?branch=master&service=github
    :alt: Coverage Status
    :target: https://coveralls.io/r/andreoliwa/python-vidsub

.. |codeclimate| image:: https://codeclimate.com/github/andreoliwa/python-vidsub/badges/gpa.svg
   :target: https://codeclimate.com/github/andreoliwa/python-vidsub
   :alt: CodeClimate Quality Status

.. |version| image:: https://img.shields.io/pypi/v/vidsub.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/vidsub

.. |wheel| image:: https://img.shields.io/pypi/wheel/vidsub.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/vidsub

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/vidsub.svg
    :alt: Supported versions
    :target: https://pypi.org/project/vidsub

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/vidsub.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/vidsub

.. |commits-since| image:: https://img.shields.io/github/commits-since/andreoliwa/python-vidsub/v0.0.0.svg
    :alt: Commits since latest release
    :target: https://github.com/andreoliwa/python-vidsub/compare/v0.0.0...master



.. end-badges

Tools to sync subtitles and fix video file names

* Free software: MIT license

Installation
============

::

    pip install vidsub

You can also install the in-development version with::

    pip install https://github.com/andreoliwa/python-vidsub/archive/master.zip


Documentation
=============


https://python-vidsub.readthedocs.io/


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
