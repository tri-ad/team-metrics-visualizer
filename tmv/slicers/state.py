"""
To implement component value saving,
when component is created, the saved value should be loaded via `load_slicer_value`
and used as inital value for component's attr (e.g. `value`)

Then in each dashboard this component is used, a callback should be added
via `callback_slicer_state_saving` to save updates of the component's attr
"""
from typing import List, Optional, Union

from dash.dependencies import Input, Output
from flask import session


def _gen_slicer_key(slicer_key: str, value_type) -> str:
    return f"{slicer_key}|{value_type.__name__}"


def save_slicer_value(slicer_key: str, value):
    if "slicers" not in session:
        session["slicers"] = {}

    if value is None:
        return

    value_type = type(value)
    key = _gen_slicer_key(slicer_key, value_type)

    session["slicers"][key] = value
    session.modified = True


def load_slicer_value(
    slicer_key: str, value_type, available_options: Optional[List] = None, default=None
):
    """Loads saved slicer's value from `slicer_key` + `value_type`

    :param slicer_key: slicer's key
    :param value_type: type of saved value.
                       It's useful in case attr can have different types
    :param available_options: (optional) to check if saved value is valid
    :param default: returned if no saved value or it's not in `available_options`
    """
    if "slicers" not in session:
        session["slicers"] = {}

    slicer_full_key = _gen_slicer_key(slicer_key, value_type)

    if slicer_full_key not in session["slicers"]:
        return default

    saved_value = session["slicers"][slicer_full_key]

    if available_options is not None:
        if isinstance(saved_value, list):
            new_options = [i for i in saved_value if i in available_options]
            if new_options:
                return new_options
            return default
        else:
            if saved_value not in available_options:
                return default

    return saved_value


def callback_slicer_state_saving(
    app, slicer_key: str, input_id: str, input_attr: Union[str, List[str]] = "value"
):
    """Add callback for saving slicer's attrs state"""
    multiple_inputs = isinstance(input_attr, (tuple, list))

    if multiple_inputs:
        inputs = [Input(input_id, attr) for attr in input_attr]
    else:
        inputs = [Input(input_id, input_attr)]

    @app.callback(Output(input_id, "id"), inputs)
    def _save_slicer_state_to_session(*args):
        save_slicer_value(slicer_key, list(args) if multiple_inputs else args[0])

        # callbacks require output, so we use `id` as dummy output
        return input_id
