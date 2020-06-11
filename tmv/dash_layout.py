import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as dhtml
from dash.dependencies import Input, Output, State
from flask import url_for


def init_tabs_for_navbar(dash_app, dashboards, path_prefix):

    pages_mapping = {}
    # Register callbacks for all dashboards and create a map of dashboards by path
    for dashboard in dashboards:
        if hasattr(dashboard, "register_callbacks"):
            dashboard.register_callbacks(dash_app)
        dashboard_url = path_prefix + dashboard.path()
        pages_mapping[dashboard_url] = dashboard

    @dash_app.callback(Output("page-content", "children"), [Input("url", "pathname")])
    # pylint: disable=unused-variable
    def render_page(pathname):
        """
        Renders the correct dashboard based on the url path.

        :param pathname: The relative path to the dashboard.
        :return: Dashboard layout.
        """

        # If it's the home url, load the first dashboard.
        # Dash does not support URL rewriting, so we redirect.
        if pathname in pages_mapping:
            dashboard = pages_mapping[pathname]
            return dbc.Container([*dashboard.dashboard()])
        elif pathname == path_prefix:
            # The root path will show the first dashboard
            # We reload the page because we can't reqrite the URL in Dash
            return dcc.Location(
                pathname=path_prefix + dashboards[0].path(), id="url", refresh=True
            )
        # Return a 404
        return dbc.Container(
            [dhtml.H1(children="Ooops!"), dhtml.H2(children="Page not found."),],
            className="text-center",
        )

    # Set the active menu item by matching the url with the dashboard path
    @dash_app.callback(
        [Output(d.path(), "active") for d in list(pages_mapping.values())],
        [Input("url", "pathname")],
    )
    # pylint: disable=unused-variable
    def toggle_active_links(pathname):
        return [pathname == path for path in list(pages_mapping.keys())]

    # Toggles the collapsible menu
    @dash_app.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")],
    )
    # pylint: disable=unused-variable
    def toggle_collapse(n_clicks, is_open):
        if n_clicks is None:
            return False
        return not is_open


USER_GREETING_ID = "dropdown-user-greeting-id"


def layout(dashboards, root_path):
    # Set up dash-app layout with dashboard links on the header.
    navbar_dropdown = dbc.Nav(
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Hi!", header=True, id=USER_GREETING_ID),
                dbc.DropdownMenuItem(divider=True),
                dbc.DropdownMenuItem("Admin", href="/admin", external_link=True),
                dbc.DropdownMenuItem(
                    "Logout", href=url_for("security.logout"), external_link=True
                ),
            ],
            nav=True,
            in_navbar=True,
            label="Account",
            right=True,
            toggleClassName="btn btn-navbar",
        ),
        className="ml-auto, d-flex flex-row order-2 order-lg-3",
    )

    collapse_menu = dbc.Collapse(
        dbc.Nav(
            [
                dbc.NavItem(dbc.NavLink(d.title(), href=d.path()), id=d.path())
                for d in dashboards
            ],
            className="mr-auto",
            navbar=True,
        ),
        id="navbar-collapse",
        className="order-3 order-lg-2",
        navbar=True,
    )

    navbar = dbc.Navbar(
        dbc.Container(
            [
                dbc.NavbarToggler(id="navbar-toggler"),
                dbc.NavbarBrand(
                    [
                        dhtml.Img(
                            src=url_for("static", filename="logo.svg"),
                            className="brand-icon",
                        )
                    ],
                    href=root_path,
                ),
                navbar_dropdown,
                collapse_menu,
            ],
        ),
        sticky="top",
        expand="lg",
    )

    content = dhtml.Div(id="page-content")

    page = [
        # represents the URL bar, doesn't render anything
        dcc.Location(id="url", refresh=False),
        navbar,
        content,
    ]

    return dhtml.Div(page)
