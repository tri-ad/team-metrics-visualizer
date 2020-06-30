Team Metrics Visualizer documentation
=====================================

How to get started?
-------------------

In order to get team metrics visualizer running, you just need to do the following:

#. Set up the tool locally: :doc:`installation`.
#. Configure it, following the provided example-file ``sample.env``: :doc:`configuration`.

After that you should be able to import data, manually or automatically through connectors and run the tool on your local machine. 
When you are ready, you can deploy it to anywhere you like. Deployment is easy and can be done manually or automated using a tool like Fabric. Refer to :doc:`deployment` for details.

Team metrics visualizer is built such that it can be easily extended to support your needs and the tools you are using. 
If you use a tool that's not supported yet by team metrics visualizer, you can write a connector to ingest its data. 
If you want to perform an analysis that's not possible with the visuals contained in team metrics visualizer, you can easily create your own visual.
Refer to the document :doc:`how_to_modify` for more information.


Contents
--------

.. toctree::
   :maxdepth: 2

   installation
   configuration
   deployment
   how_to_modify
   connectors
   dashboards
   slicers
   visuals
   structure
   adding_data
   reference
   faqs



Indices and tables
==================

+ :ref:`genindex`
+ :ref:`modindex`
+ :ref:`search`

