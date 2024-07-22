import datetime
import threading
from collections import OrderedDict
import logging

from dash import Dash, html, dcc, callback, Input, Output, State, callback, dash_table
import pandas as pd
import dash_bootstrap_components as dbc
import numpy as np

external_stylesheets = [dbc.themes.BOOTSTRAP]

app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
)
logging.getLogger("werkzeug").setLevel(logging.CRITICAL)

df = pd.DataFrame


class LocalWebServer(object):
    """
    Test web server using dash/plotly.
    """

    def __init__(self) -> None:

        self.app = app  # global
        self.df = df
        self.port = 2403
        self.logcommands = 0
        self.logstatus = 0

        self.data = {
            "Parameter": [
                "Image Filename",
                "Image Title",
                "Image Type",
                "Exposure Time",
                "Test Image",
                "Temperatures",
                "Binning",
                "Mode",
                "Messages",
                "Timestamp",
                "Progress",
                "Message",
            ],
            "Value": [
                "filename",
                "title",
                "type",
                "time",
                "test",
                "temp",
                "bin",
                "mode",
                "messages",
                "timestamp",
                "progress",
                "message",
            ],
        }

        self.create_page()

    def create_page(self):
        """
        Create status page.
        """

        def getData():
            data = self.data
            df = pd.DataFrame(data)
            now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            df.at[9, "Value"] = now

            out = df.to_dict("records")
            return out

        # tabs = Exposure Filename Detector Options

        button_group = dbc.ButtonGroup(
            [
                dbc.Button("Expose", id="expose_btn", className="me-1", n_clicks=0),
                dbc.Button("Sequence", id="sequence_btn", className="me-1", n_clicks=0),
                dbc.Button("Reset", id="reset_btn", className="me-1", n_clicks=0),
                dbc.Button("Abort", id="abort_btn", className="me-1", n_clicks=0),
                dbc.Button(
                    "Save Pars", id="savepars_btn", className="me-1", n_clicks=0
                ),
            ],
            vertical=True,
        )

        # image type and exposure time
        # image title
        # test image
        # num seq images Seq delay
        # sequence flush

        image_type_dropdown = html.Div(
            [
                dbc.Label("Image Type"),
                dcc.Dropdown(
                    options=[
                        {"label": "Zero", "value": "zero"},
                        {"label": "Object", "value": "object"},
                        {"label": "Flat", "value": "flat"},
                        {"label": "Dark", "value": "dark"},
                    ],
                    id="image_type_dropdown",
                    value="zero",
                ),
                html.P(id="image_type"),
            ]
        )

        @callback(
            Output("image_type", "children"), [Input("image_type_dropdown", "value")]
        )
        def image_type_callback(value):
            print(value)
            return value

        exposure_time_input = dcc.Input(id="et", type="number", min=0, step=1)

        image_title_input = html.Div(
            [
                dbc.Label("Image Title"),
                dcc.Input(
                    id="title_input",
                    placeholder="Enter image title...",
                    type="text",
                    style={"display": "inline-block", "border": "1px solid black"},
                ),
                html.P(id="image_title"),
            ]
        )

        @callback(Output("image_title", "children"), [Input("title_input", "value")])
        def image_title_callback(value):
            return value

        card1 = dbc.Card(
            dbc.CardBody(
                [
                    html.H5("AzCam Camera Control", className="card-title"),
                    html.P("This card has some text content, but not much else"),
                ]
            )
        )

        card4 = dbc.Card(
            dbc.CardBody(
                [
                    image_title_input,
                    image_type_dropdown,
                    exposure_time_input,
                ]
            )
        )

        card2 = dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Exposure Control", className="card-title"),
                    dbc.Row(
                        [
                            dbc.Col(button_group, width=3),
                            dbc.Col(card4, width=3),
                        ]
                    ),
                ]
            )
        )

        card3 = dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Status", className="card-title"),
                    dash_table.DataTable(
                        id="table",
                        data=getData(),
                        # columns=[{"id": c, "name": c} for c in self.df.columns],
                        cell_selectable=False,
                        editable=False,
                    ),
                ]
            )
        )

        card_test = dbc.Card(dbc.CardBody(["not yet..."]))

        exposure_tab = [
            # card1,
            card2,
            card3,
        ]

        filename_tab = [
            card_test,
        ]

        detector_tab = [
            card_test,
        ]

        options_tab = [
            card_test,
        ]

        tabs = dbc.Tabs(
            [
                dbc.Tab(exposure_tab, label="Exposure"),
                dbc.Tab(filename_tab, label="Filename"),
                dbc.Tab(detector_tab, label="Detector"),
                dbc.Tab(options_tab, label="Options"),
            ]
        )

        self.app.layout = html.Div(
            [
                tabs,
                dcc.Interval("table-update", interval=1_000, n_intervals=0),
            ]
        )

        # status table update
        @callback(
            Output("table", "data"),
            Input("table-update", "n_intervals"),
        )
        def update(n):
            return getData()

        # button clicks
        @callback(
            Output("message", "children"),
            Input("expose_btn", "n_clicks"),
        )
        def on_button_click_exposose(n):
            if n is None:
                return "Not clicked."
            else:
                return f"Expose Clicked {n} times."

        @callback(
            Input("sequence_btn", "n_clicks"),
        )
        def on_button_click_sequence(n):
            if n is None:
                return "Not clicked."
            else:
                return f"Sequence Clicked {n} times."

        return

    def start(self):
        # arglist = [self.app]
        kwargs = {"debug": False, "port": "2403", "host": "", "use_reloader": False}
        # kwargs = {}

        if 0:
            thread = threading.Thread(
                target=self.app.run,
                name="azcam_webserver",
                kwargs=kwargs,
            )
            thread.daemon = True  # terminates when main process exits
            thread.start()
        else:
            self.app.run(port="2403", debug=True)


if __name__ == "__main__":
    webserver = LocalWebServer()
    # webserver.app.run(debug=True)
    webserver.start()
    # input("waiting for web server here...")
