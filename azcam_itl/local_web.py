"""
DASH / Plotly web server for azcam
"""

import datetime
import threading
import logging

from dash import Dash, html, dcc, callback, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import dash_daq as daq

import pandas as pd
import numpy as np

import azcam


class WebServerDash(object):
    """
    Test web server using dash/plotly.
    """

    def __init__(self) -> None:

        self.port = 2403
        self.logcommands = 0
        self.logstatus = 0
        azcam.db.webserver = self
        azcam.db._webdata = {"filename": "", "timestamp": "", "exposuretime": ""}
        df = pd.DataFrame

        self.app = Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True,
        )
        logging.getLogger("werkzeug").setLevel(logging.CRITICAL)  # stop messages

        self.create_page()

    def create_page(self):
        """
        Create web page.
        """

        #############################################################
        # buttons card
        #############################################################
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
        buttons_card = dbc.Card(dbc.CardBody([button_group]))

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

        #############################################################
        # exposure card
        #############################################################

        image_type_dropdown = html.Div(
            [
                dbc.Label("Image Type"),
                dcc.Dropdown(
                    options=[
                        {"label": "Zero", "value": "zero"},
                        {"label": "Object", "value": "object"},
                        {"label": "Flat", "value": "flat"},
                        {"label": "Dark", "value": "dark"},
                        {"label": "Comps", "value": "comps"},
                    ],
                    id="image_type_dropdown",
                    value="zero",
                ),
                html.Div(id="hidden_image_type", hidden=True),
            ]
        )

        @callback(
            Output("hidden_image_type", "children"),
            [Input("image_type_dropdown", "value")],
        )
        def image_type_callback(value):
            return ""

        exposure_time_input = html.Div(
            [
                daq.NumericInput(id="et", value=0.0, label="Exposure time [sec]"),
            ]
        )

        image_title_input = html.Div(
            [
                dbc.Label("Image Title"),
                dbc.Input(
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

        test_image_input = html.Div(
            [
                daq.BooleanSwitch(
                    id="test_image", label="Test Image", on=True, color="#00AA00"
                ),
                html.Div(id="test-image_switch_output", hidden=True),
            ]
        )

        card_exposure_control = dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Exposure", className="card-title"),
                    dbc.Row(
                        [
                            dbc.Col(image_type_dropdown),
                            dbc.Col(test_image_input),
                            dbc.Col(exposure_time_input),
                        ]
                    ),
                    dbc.Row(
                        [
                            image_title_input,
                        ]
                    ),
                ]
            )
        )

        #############################################################
        # sequence card
        #############################################################
        num_seq_images_input = html.Div(
            [
                daq.NumericInput(id="seq_num", label="Number images"),
            ]
        )
        sequence_delay_input = html.Div(
            [
                daq.NumericInput(id="seq_delay", label="Seq. delay [sec]"),
            ]
        )
        card_sequence = dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Sequence", className="card-title"),
                    dbc.Row(
                        [
                            dbc.Col(num_seq_images_input, width=6),
                            dbc.Col(sequence_delay_input),
                        ]
                    ),
                ]
            )
        )

        #############################################################
        # exposure control card
        #############################################################
        card_exposure = dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Exposure Control", className="card-title"),
                    dbc.Row(
                        [
                            dbc.Col(buttons_card, width=2),
                            dbc.Col(card_exposure_control, width=6),
                            dbc.Col(card_sequence, width=4),
                        ]
                    ),
                ]
            )
        )

        #############################################################
        # status card
        #############################################################
        # table_header = [
        #     html.Thead(html.Tr([html.Th("First Name"), html.Th("Last Name")]))
        # ]

        row1 = html.Tr(
            [
                html.Td("Image Filename"),
                html.Td("filename here", id="filename_status", colSpan=3),
            ]
        )
        row2 = html.Tr(
            [
                html.Td("Image Title"),
                html.Td("title here", id="imagetitle_status", colSpan=3),
            ]
        )
        row3 = html.Tr(
            [
                html.Td("Image Type"),
                html.Td("type here", id="imagetype_status"),
                html.Td("Exposure Time"),
                html.Td("ET here", id="et_status"),
            ]
        )
        row4 = html.Tr(
            [
                html.Td("Test Image"),
                html.Td("test here", id="imagetest_status"),
                html.Td("Mode"),
                html.Td("mode here", id="mode_status"),
            ]
        )
        row5 = html.Tr(
            [
                html.Td("Temperatures"),
                html.Td("temps here", id="temps_status"),
                html.Td("Binning"),
                html.Td("binning here", id="binning_status"),
            ]
        )
        row6 = html.Tr(
            [
                html.Td("Messages"),
                html.Td("messages here", id="messages_status", colSpan=3),
            ]
        )
        row7 = html.Tr(
            [
                html.Td("Timestamp"),
                html.Td("timestamp here", id="timestamp_status", colSpan=3),
            ]
        )
        row8 = html.Tr(
            [
                html.Td("Progress"),
                html.Td("progress here", id="progress_status", colSpan=3),
            ]
        )

        table_body = [html.Tbody([row1, row2, row3, row4, row5, row6, row7, row8])]
        table = dbc.Table(
            table_body,
            bordered=True,
            striped=True,
            dark=False,
            style={"padding": "2em"},
        )
        # table = dbc.Table(table_header + table_body, bordered=True)

        card_status = dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Status for Current Exposure", className="card-title"),
                    table,
                ]
            )
        )

        # status table update
        @callback(
            Output("filename_status", "children"),
            Input("update_status1", "n_intervals"),
        )
        def get_status1(n):
            filename = azcam.db._webdata["filename"]
            return filename

        @callback(
            Output("et_status", "children"),
            Input("update_status2", "n_intervals"),
        )
        def get_status2(n):
            et = azcam.db._webdata["exposuretime"]
            return et

        @callback(
            Output("timestamp_status", "children"),
            Input("update_status3", "n_intervals"),
        )
        def get_status3(n):
            ts = azcam.db._webdata["timestamp"]
            return ts

        #############################################################
        # still undefined cards
        #############################################################
        card_test = dbc.Card(dbc.CardBody(["not yet..."]))

        #############################################################
        # tabs
        #############################################################
        exposure_tab = [
            dbc.CardBody(
                [
                    card_exposure,
                    card_status,
                    html.Div("", id="null1", hidden=True),
                ]
            )
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

        #############################################################
        # layout
        #############################################################
        self.app.layout = html.Div(
            [
                tabs,
                dcc.Interval("update_status", interval=1_000, n_intervals=0),
                dcc.Interval("update_status1", interval=1_000, n_intervals=0),
                dcc.Interval("update_status2", interval=1_000, n_intervals=0),
                dcc.Interval("update_status3", interval=1_000, n_intervals=0),
            ]
        )

        @callback(
            Output("null1", "children"),
            Input("update_status", "n_intervals"),
        )
        def get_status(n):
            azcam.db._webdata = azcam.db.tools["exposure"].get_status()
            return

    def start(self):
        # arglist = [self.app]
        kwargs = {"debug": False, "port": "2403", "host": "", "use_reloader": False}
        # kwargs = {}

        if 1:
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
    webserver = WebServerDash()
    webserver.app.run(debug=True, port=2403, reload=True)
    # webserver.start()
    input("waiting for web server here...")
