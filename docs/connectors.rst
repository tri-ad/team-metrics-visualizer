Connectors to other systems
===========================

The ``connectors``-package contains packages for ingesting data from various systems. 
A connector can periodically check for new data and import it (via Celery_). 
It could also load & process data from a file uploaded to the system, e.g. a spreadsheet or CSV-file. 
For the latter, there is an abstract baseclass ``shared.FileImporter``, which should be extended.

Available connectors
--------------------

.. toctree::

    connectors.jira
    connectors.overtime
    connectors.TeamHealthCheck

Code shared among connectors
----------------------------

.. automodule:: connectors.shared
    :members:
    :undoc-members:
    :show-inheritance:


Module contents
---------------

.. automodule:: connectors
    :members:
    :undoc-members:
    :show-inheritance:

.. _Celery: https://docs.celeryproject.org/