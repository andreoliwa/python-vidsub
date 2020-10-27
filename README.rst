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
.. |docs| image:: https://readthedocs.org/projects/python-video-tools/badge/?style=flat
    :target: https://readthedocs.org/projects/python-video-tools
    :alt: Documentation Status

.. |travis| image:: https://api.travis-ci.org/andreoliwa/python-video-tools.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/andreoliwa/python-video-tools

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/andreoliwa/python-video-tools?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/andreoliwa/python-video-tools

.. |requires| image:: https://requires.io/github/andreoliwa/python-video-tools/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/andreoliwa/python-video-tools/requirements/?branch=master

.. |coveralls| image:: https://coveralls.io/repos/andreoliwa/python-video-tools/badge.svg?branch=master&service=github
    :alt: Coverage Status
    :target: https://coveralls.io/r/andreoliwa/python-video-tools

.. |codeclimate| image:: https://codeclimate.com/github/andreoliwa/python-video-tools/badges/gpa.svg
   :target: https://codeclimate.com/github/andreoliwa/python-video-tools
   :alt: CodeClimate Quality Status

.. |version| image:: https://img.shields.io/pypi/v/video-tools.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/video-tools

.. |wheel| image:: https://img.shields.io/pypi/wheel/video-tools.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/video-tools

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/video-tools.svg
    :alt: Supported versions
    :target: https://pypi.org/project/video-tools

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/video-tools.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/video-tools

.. |commits-since| image:: https://img.shields.io/github/commits-since/andreoliwa/python-video-tools/v0.0.0.svg
    :alt: Commits since latest release
    :target: https://github.com/andreoliwa/python-video-tools/compare/v0.0.0...master



.. end-badges

Tools to sync subtitles and fix video file names

* Free software: MIT license

Installation
============

::

    pip install video-tools

You can also install the in-development version with::

    pip install https://github.com/andreoliwa/python-video-tools/archive/master.zip


Documentation
=============


https://python-video-tools.readthedocs.io/


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
