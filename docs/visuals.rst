Visuals
=======

Visuals are the graphs and data tables that make up dashboards. You can reuse visuals 
in multiple dashboards.  This is how a visual looks like:

.. image:: _static/chart_burnup.png
   :width: 100%
   :alt: A burnup chart

You can filter the data in visuals by using one of the pre-made
slicers described in :doc:`slicers` or you can create your own. This is how a slicer 
looks like:

.. image:: _static/date_range_slicer.png
   :width: 300
   :alt: A slicer for date-ranges

If you want to create your own visuals, a good starting point is to subclass the 
base-classes in ``visuals.base``.

When you are done, you can add your new visual to a dashboard. See :doc:`dashboards` for
details on that.

visuals.base module
-------------------

.. automodule:: visuals.base
   :members:
   :undoc-members:
   :show-inheritance:

visuals.burnup module
---------------------

.. automodule:: visuals.burnup
   :members:
   :undoc-members:
   :show-inheritance:

visuals.cumulative\_flow module
-------------------------------

.. automodule:: visuals.cumulative_flow
   :members:
   :undoc-members:
   :show-inheritance:

visuals.shared module
---------------------

.. automodule:: visuals.shared
   :members:
   :undoc-members:
   :show-inheritance:

visuals.team\_health\_check module
----------------------------------

.. automodule:: visuals.team_health_check
   :members:
   :undoc-members:
   :show-inheritance:

visuals.work\_time module
-------------------------

.. automodule:: visuals.work_time
   :members:
   :undoc-members:
   :show-inheritance:
