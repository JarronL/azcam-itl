import datetime
import threading
from collections import OrderedDict
import logging

from dash import Dash, html, dcc, callback, Input, Output, State, callback, dash_table
import pandas as pd
import dash_bootstrap_components as dbc
import numpy as np

external_stylesheets = [dbc.themes.BOOTSTRAP]

app = Dash(__name__, external_stylesheets=external_stylesheets)
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
            "Status": [
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

        button_group = dbc.ButtonGroup(
            [
                dbc.Button("Expose", id="expose_btn", className="me-1", n_clicks=0),
                dbc.Button("Sequence", id="sequence_btn", className="me-1", n_clicks=0),
                dbc.Button("Filename", id="filename_btn", className="me-1", n_clicks=0),
                dbc.Button("Detector", id="detector_btn", className="me-1", n_clicks=0),
                dbc.Button("Abort", id="abort_btn", className="me-1", n_clicks=0),
            ],
            vertical=True,
        )

        self.app.layout = html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(button_group, width=3),
                        dbc.Col(
                            dash_table.DataTable(
                                id="table",
                                data=getData(),
                                # columns=[{"id": c, "name": c} for c in self.df.columns],
                                cell_selectable=False,
                                editable=False,
                            ),
                            width=6,
                        ),
                    ]
                ),
                html.Span(id="message", style={"verticalAlign": "middle"}),
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
