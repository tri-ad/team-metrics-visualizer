import urllib.parse
from abc import ABC, abstractmethod
from typing import List

import dash_html_components as dhtml
from dash_bootstrap_components import Col, Row
from dash_html_components import Div

from database import db


class DashboardController(ABC):
    """
    Abstract base class for creating dashboards.

    To create a new dashboard,

    1. subclass `DashboardController` and implement the functions
       `title()`, `dashboard()` and `register_callbacks()`.
    2. `title()` should return a short string which becomes the label of the tab in which the dashboard appears.
    3. `dashboard()` should return a list of dash-components & interface elements
       which will get displayed on a page or in a tab. This should include all
       your slicers and visuals. You can use the method `standard_layout()`,
       which provides you with a basic layout for your dashboard.
    4. `register_callbacks()` can be used to register callbacks from controls to
       update visuals (or other controls) in the dashboard. Look at other
       dashboards for examples. If you don't need any callbacks, you still
       need to implement this method. Note that `register_callbacks()` does
       not return anything.
    5. If you implement `register_callbacks()`, you need to do the following
       imports to be able to specify input & output of the callback::

           from dash.dependencies import Input, Output

    After having implemented your subclass, you can include it in the app by
        adding the following to app.py:
        1. Create an instance of it: mydash = MyDashboard()
        2. Add it to the TABS-list: `TABS.append(mydash)`
    All dashboards which are in the TABS-list automatically get their callbacks
        registered (in app.py, `register_callbacks()` gets called.)
    """

    STANDARD_LAYOUT_SLICER_BAR_WIDTH = 2

    @abstractmethod
    def title(self) -> str:
        """ Return title of the dashboard """
        pass

    def path(self) -> str:
        """ Return the path of the dashboard """
        return urllib.parse.quote(self.title().lower().replace(" ", "_"))

    @abstractmethod
    def dashboard(self) -> List:
        """ Returns `List` of controls and visuals for the dashboard. """
        pass

    @abstractmethod
    def register_callbacks(self, app):
        """
        Registers callbacks for controls to update visuals (or other controls).

        :param app: Pass the instance of your Dash-app
        """
        pass

    def visuals_wrapper(self, visuals):
        """Wraps each visual into a card in standard layouts"""
        return [
            dhtml.Div(className="chart-card", children=[visual]) for visual in visuals
        ]

    def standard_layout(self, controls=[], visuals=[]) -> List:
        """
        Return a basic layout with controls on the left and visuals in the
        center of the screen.

        :param controls: The controls (slicers etc.) of your dashboard as a `List`
        :param visuals: The visuals (charts etc.) of your dashboard as a `List`

        This function can be used in your implementation of dashboard() like
        this::

            def dashboard(self) -> List:
                return standard_layout(
                    controls = [control1, control2, ...],
                    visuals = [visual1, visual2, ...]
                )
        """
        return [
            Row(
                [
                    Col(
                        width=12,
                        children=[Div(className="slicers-card", children=controls)],
                    ),
                ]
            ),
            Row(
                [Col(width=12, children=[Div(children=self.visuals_wrapper(visuals))])],
                justify="start",
            ),
        ]

    def standard_grid_layout(self, controls=[], visuals=[]) -> List:
        """
        Returns a basic layout with controls on the left and visuals in a
        2xn-grid next to it.

        See :meth:`standard_layout` for details on how to implement.
        """
        return [
            Row(
                [
                    Col(
                        width=12,
                        children=Div(className="slicers-card", children=controls),
                    ),
                ]
            ),
            Row(
                [
                    Col(width=6, children=self.visuals_wrapper(visuals[::2])),
                    Col(width=6, children=self.visuals_wrapper(visuals[1::2])),
                ],
                justify="start",
            ),
        ]
