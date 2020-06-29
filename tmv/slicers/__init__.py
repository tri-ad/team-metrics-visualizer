import slicers.dates as dates
import slicers.organization as org
import slicers.team_health_check as thc

"""
    Shared Controls

    These are controls you can use in your dashboards. They provide slicing
    by common parameters like date, teams etc.
    Each of the methods in this module returns a List of dash-elements. It is a list
    because some controls may actually be made up of several dash elements,
    like for example the control itself and a label.
    After adding the control to your dashboard, you can connect it to your
    visuals by defining a callback in the register_callbacks()-method of your
    dashboard-class. When using the controls, be careful that you assign a
    unique html_element_id to it! If you give two controls the same id, dash
    will throw an error and your callbacks will not work.
"""
