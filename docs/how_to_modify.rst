How to make modifications
=========================

This document gives a brief description on how to extend the tool to your needs. You can extend the tool in various ways:

+ Writing a connector to a tool you use and ingest its data.
+ Creating a new dashboard using existing visuals (graphs etc.).
+ Creating your own visuals.
+ Create new views for the admin-area, for example for maintaining your new connector's data.

Scroll down to the end of this page to find references for the modules you will need to extend.

How to write a connector to some system
---------------------------------------
+ Create a new python-module (containing ``__init.py__``) in directory ``connectors``.
+ You can re-use or add code to ``tmv/connectors/shared.py`` in case it may be shared among other connectors.
+ If you are importing files (Excel, CSV, ...), please start by subclassing ``FileImporter`` in ``tmv/connectors/shared.py``. If it does not work with your files, consider extending it without breaking the current API.

How to create a new dashboard using existing visuals
----------------------------------------------------
+ Create a new file in directory ``dashboards`` and start by subclassing the ``Dashboard``-class in ``tmv/dashboards/base.py``.
+ You need to at least implement the methods ``title()`` and ``dashboard()``. If you need callbacks, implement them in ``register_callbacks()``.
+ See the comments in ``tmv/dashboards/base.py`` for how to integrate your dashboard in the app or a tab bar.
+ _Hint_: The function ``standard_layout()`` of the ``Dashboard``-class is helpful if you want to quickly create a dashboard with a basic layout!

How to create a new visual
--------------------------
+ Create a new file in directory ``visuals`` and start by subclassing the ``VisualController``-class in ``tmv/visuals/base.py``.
+ You need to at least implement the methods ``draw()`` and ``update()``. The first one is responsible for initially drawing your visual (and providing initial values for the respective filters), while the second one updates it after some filters have changed.
+ A good practice is to use ``update()`` in ``draw()`` and provide it with initial values for filters.
+ See above on how to add your visual to one (or several) dashboards.
+ _Important:_ When filtering data via inputs, do not modify global variables or instance-variables of your visual. If you do this, the app will not work for multiple users, as they overwrite each other's data. See here for details: https://dash.plot.ly/sharing-data-between-callbacks

How to add a view to the admin-area
-----------------------------------

Case 1: Add to existing blueprint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If your page would be a part of the existing blueprints in ``tmv/views/`` (for example: _admin_), please add it to the existing file by creating a new route (example is for blueprint _admin_):

.. code-block:: python

    @admin.route('/admin/cool-stuff')
    def admin_cool_stuff_page():
        return ('Great new feature for admin!')

You don't have to do anything else, the new route will be registered with the server and (in this example) will be available at ``HOSTNAME:PORT/admin/cool-stuff``.


Case 2: Create a new blueprint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In case you want to create an entirely new section (for example: _guestbook_ ;-)) of the system, it makes sense to create a new file ``guestbook.py`` in ``tmv/views/``. Start with this:

.. code-block:: python

    from flask import Blueprint
    guestbook = Blueprint('guestbook', __name__)


Then add your routes as described above.
After this is done, register your new blueprint in ``tmv/app.py`` like so:

.. code-block:: python

    from views.guestbook import guestbook
    [...]
    server.register_blueprint(guestbook)


That's it!

.. toctree::
   :maxdepth: 3
   
   connectors
   dashboards
   views
   visuals