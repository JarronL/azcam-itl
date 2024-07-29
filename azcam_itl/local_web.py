"""
DASH / Plotly web server for azcam
"""

import threading
import logging

from dash import Dash, html, dcc, callback, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import dash_daq as daq

import azcam


class WebServerDash(object):
    """
    Test web server using dash/plotly.
    """

    def __init__(self) -> None:

        self.port = 2403
        self.logcommands = 0
        self.logstatus = 0

        self.button_group = None
        self.exposure_card = None

        azcam.db.webserver = self
        azcam.db._command = {}  # command dict

        self.create_app()

        self.create_buttons()
        self.create_exposure_card()
        self.create_sequence_card()
        self.create_control_card()
        self.create_status_card()
        self.create_filename_card()
        self.create_detector_card()
        self.create_options_card()

        self.create_layout()

    def create_app(self):

        self.app = Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=False,
        )
        logging.getLogger("werkzeug").setLevel(logging.CRITICAL)  # stop messages

        return

    def create_buttons(self):
        """
        Create button group for exposure control.
        """

        self.button_group = dbc.ButtonGroup(
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

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("expose_btn", "n_clicks"),
            prevent_initial_call=True,
        )
        def on_button_click_expose(n):
            try:
                azcam.db.tools["exposure"].expose()
            except Exception as e:
                print(e)
            return

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("sequence_btn", "n_clicks"),
            prevent_initial_call=True,
        )
        def on_button_click_sequence(n):
            try:
                azcam.db.tools["exposure"].sequence()
            except Exception as e:
                print(e)
            return

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("reset_btn", "n_clicks"),
            prevent_initial_call=True,
        )
        def on_button_click_reset(n):
            try:
                azcam.db.tools["exposure"].reset()
            except Exception as e:
                print(e)
            return

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("abort_btn", "n_clicks"),
            prevent_initial_call=True,
        )
        def on_button_click_abort(n):
            try:
                azcam.db.tools["exposure"].abort()
            except Exception as e:
                print(e)
            return

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("savepars_btn", "n_clicks"),
            prevent_initial_call=True,
        )
        def on_button_click_savepars(n):
            try:
                azcam.db.parameters.save_pars()
            except Exception as e:
                print(e)
            return

        return

    def create_exposure_card(self):
        """
        Create exposure card for exposure control.
        """

        options = [
            {"label": x, "value": x.lower()}
            for x in azcam.db.tools["exposure"].image_types
        ]

        image_type_dropdown = html.Div(
            [
                dbc.Label("Image Type"),
                dcc.Dropdown(
                    options,
                    id="image_type_dropdown",
                    value="zero",
                ),
            ]
        )

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("image_type_dropdown", "value"),
            prevent_initial_call=True,
        )
        def image_type_callback(value):
            azcam.db._command["image_type"] = value
            azcam.db.tools["exposure"].message = repr(azcam.db._command)
            return ""

        exposure_time_input = html.Div(
            [
                dbc.Label("Exp. time [sec]"),
                daq.NumericInput(id="et", value=0.0, size=100),
            ]
        )

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("et", "value"),
            prevent_initial_call=True,
        )
        def exposure_time_callback(value):
            azcam.db._command["exposure_time"] = value
            azcam.db.tools["exposure"].message = repr(azcam.db._command)
            return ""

        image_title_input = html.Div(
            [
                dbc.Label("Image Title"),
                dbc.Input(
                    id="title_input",
                    placeholder="Enter image title...",
                    type="text",
                    style={"display": "inline-block"},
                ),
            ]
        )

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("title_input", "value"),
            prevent_initial_call=True,
        )
        def image_title_callback(value):
            azcam.db._command["image_title"] = "" if value is None else value
            azcam.db.tools["exposure"].message = repr(azcam.db._command)
            return value

        test_image_input = html.Div(
            [
                dbc.Label("Test Image"),
                dbc.Checkbox(id="test_image", value=True),
            ]
        )

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("test_image", "value"),
            prevent_initial_call=True,
        )
        def image_test_callback(value):
            azcam.db._command["test_image"] = value
            azcam.db.tools["exposure"].message = repr(azcam.db._command)
            return value

        self.exposure_card = dbc.Card(
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

        return

    def create_sequence_card(self):
        """
        Create sequence control card.
        """

        num_seq_images_input = html.Div(
            [
                daq.NumericInput(id="seq_num", label="Number images", size=100),
            ]
        )

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("seq_num", "value"),
            prevent_initial_call=True,
        )
        def seq_total_callback(value):
            azcam.db._command["seq_total"] = 0 if value is None else value
            azcam.db.tools["exposure"].message = repr(azcam.db._command)
            return value

        sequence_delay_input = html.Div(
            [
                daq.NumericInput(id="seq_delay", label="Seq. delay [sec]", size=100),
            ]
        )

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("seq_delay", "value"),
            prevent_initial_call=True,
        )
        def seq_delay_callback(value):
            azcam.db._command["seq_del"] = 0.0 if value is None else value
            azcam.db.tools["exposure"].message = repr(azcam.db._command)
            return value

        self.sequence_card = dbc.Card(
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

        return

    def create_control_card(self):
        """
        Create control card for exposures.
        """

        self.control_card = dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Camera Control", className="card-title"),
                    dbc.Row(
                        [
                            dbc.Col(self.button_group, width=2),
                            dbc.Col(self.exposure_card, width=6),
                            dbc.Col(self.sequence_card, width=4),
                        ]
                    ),
                ]
            )
        )

        return

    def create_status_card(self):
        """
        Create status card.
        """
        # status card
        style1 = {"font-style": "italic"}

        row1 = html.Tr(
            [
                html.Td("Image Filename", style=style1),
                html.Td("filename here", id="filename_status", colSpan=3),
            ]
        )
        row2 = html.Tr(
            [
                html.Td("Image Title", style=style1),
                html.Td("title here", id="imagetitle_status", colSpan=3),
            ]
        )
        row3 = html.Tr(
            [
                html.Td("Image Type", style=style1),
                html.Td("type here", id="imagetype_status"),
                html.Td("Exposure Time", style=style1),
                html.Td("ET here", id="et_status"),
            ]
        )
        row4 = html.Tr(
            [
                html.Td("Test Image", style=style1),
                html.Td("test here", id="imagetest_status"),
                html.Td("Mode", style=style1),
                html.Td("mode here", id="mode_status"),
            ]
        )
        row5 = html.Tr(
            [
                html.Td("Temperatures", style=style1),
                html.Td("temps here", id="temps_status"),
                html.Td("Binning", style=style1),
                html.Td("binning here", id="binning_status"),
            ]
        )
        row_messsage = html.Tr(
            [
                html.Td("Message", style=style1),
                html.Td("messages here", id="message_status", colSpan=3),
            ]
        )
        row_ts = html.Tr(
            [
                html.Td("Timestamp", style=style1),
                html.Td("timestamp here", id="timestamp_status", colSpan=3),
            ]
        )
        row_progress = html.Tr(
            [
                html.Td("Progress", style=style1),
                html.Td(
                    dbc.Progress(id="progress_status"),
                    colSpan=3,
                ),
            ]
        )

        table_body = [
            html.Tbody(
                [row1, row2, row3, row4, row5, row_progress, row_ts, row_messsage]
            )
        ]
        table = dbc.Table(
            table_body,
            bordered=True,
            striped=True,
            dark=False,
            style={"padding": "2em"},
        )
        # table = dbc.Table(table_header + table_body, bordered=True)

        self.status_card = dbc.Card(
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                html.H4(
                                    "Status for Current Exposure",
                                    className="card-title",
                                )
                            ),
                            dbc.Col(
                                html.Div(
                                    "",
                                    id="estate_status",
                                    style={"font-weight": "bold"},
                                )
                            ),
                        ]
                    ),
                    table,
                ]
            )
        )

        # status table update
        @callback(
            Output("filename_status", "children"),
            Output("imagetitle_status", "children"),
            Output("imagetype_status", "children"),
            Output("et_status", "children"),
            Output("imagetest_status", "children"),
            Output("mode_status", "children"),
            Output("temps_status", "children"),
            Output("binning_status", "children"),
            Output("timestamp_status", "children"),
            Output("estate_status", "children"),
            Output("progress_status", "value"),
            Output("message_status", "children"),
            Input("status_interval", "n_intervals"),
        )
        def update_status(n):
            """
            Get exposure status and update fields.
            """

            webdata = azcam.db.tools["exposure"].get_status()

            # the return order must match Output order
            filename = webdata["filename"]
            imagetitle = webdata["imagetitle"]
            imagetype = webdata["imagetype"]
            et = webdata["exposuretime"]
            imagetest = webdata["imagetest"]
            mode = webdata["mode"]

            camtemp = float(webdata["camtemp"])
            dewtemp = float(webdata["dewtemp"])
            temps = f"Camera: {camtemp:.01f} C    Dewar: {dewtemp:.01f} C"

            colbin = webdata["colbin"]
            rowbin = webdata["rowbin"]
            binning = f"RowBin: {rowbin}    ColBin: {colbin}"

            ts = webdata["timestamp"]
            estate = webdata["exposurestate"]
            progress = float(webdata["progressbar"])
            message = webdata["message"]

            return [
                filename,
                imagetitle,
                imagetype,
                et,
                imagetest,
                mode,
                temps,
                binning,
                ts,
                estate,
                progress,
                message,
            ]

        return

    def create_filename_card(self):
        """
        Create filename card.
        """

        """
        Directory with browse
        Rootname
        Seq Num spinner
        Image Format NO
        
        Auto inc
        Overwrite
        Inc. seq
        Autoname
        test image
        """

        curfolder = "/data"

        folderselect = html.Div(
            [
                dbc.Label("Image folder"),
                dbc.Input(
                    id="folderselect",
                    placeholder="Enter image file folder...",
                    type="text",
                    style={"display": "inline-block"},
                ),
            ]
        )

        rootselect = html.Div(
            [
                dbc.Label("Image root name"),
                dbc.Input(
                    id="rootselect",
                    placeholder="Enter image root name...",
                    type="text",
                    style={"display": "inline-block"},
                ),
            ]
        )

        seqnumselect = html.Div(
            [
                dbc.Label("Image sequence number"),
                dbc.Input(
                    id="seqnumselect",
                    placeholder="Enter image sequence number...",
                    type="number",
                    min=0,
                    style={"display": "inline-block"},
                ),
            ]
        )

        filenamechecks_input = dcc.Checklist(
            [
                {
                    "label": "Auto increment",
                    "value": "autoinc",
                    "title": "check to auto increment image sequence number",
                },
                {
                    "label": "Overwrite existing image",
                    "value": "overwrite",
                },
                {
                    "label": "Include sequence number",
                    "value": "includeseqnum",
                },
                {
                    "label": "Auto name",
                    "value": "autoname",
                    "title": "check to inlcude Object Type in image filename",
                },
            ],
            id="filename_checks",
            value=["overwrite"],
            inline=False,
        )
        checks_filename = html.Div(filenamechecks_input)

        @callback(
            Output("hidden_div", "children", allow_duplicate=True),
            Input("filename_checks", "value"),
            prevent_initial_call=True,
        )
        def image_test_callback(value):
            azcam.db.tools["exposure"].message = repr(value)
            return value

        # apply button - all options on this page
        apply_filename_btn = dbc.Button(
            "Apply All",
            id="apply_filename_btn",
            style={"margin-top": "1em"},
            n_clicks=0,
        )

        @callback(
            Output("fileselect_out", "children", allow_duplicate=True),
            Input("apply_filename_btn", "n_clicks"),
            State("seqnumselect", "value"),
            State("rootselect", "value"),
            State("folderselect", "value"),
            prevent_initial_call=True,
        )
        def on_button_click_apply_filename(n, seqnum, root, folder):
            print(seqnum, root, folder)
            try:
                pass
                # azcam.db.tools["exposure"].expose()
            except Exception as e:
                print(e)
            return

        self.filename_card = dbc.Card(
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    folderselect,
                                    rootselect,
                                    seqnumselect,
                                ]
                            ),
                            dbc.Col(
                                [
                                    checks_filename,
                                ]
                            ),
                        ]
                    ),
                    dbc.Row(
                        [
                            apply_filename_btn,
                            html.Div(id="fileselect_out"),
                        ]
                    ),
                ]
            )
        )

        return

    def create_detector_card(self):
        """
        Create detector card.
        """

        self.detector_card = dbc.Card(dbc.CardBody([html.Div("Detector not yet")]))

        return

    def create_options_card(self):
        """
        Create options card.
        """

        self.options_card = dbc.Card(dbc.CardBody([html.Div("Options not yet")]))

        return

    def create_layout(self):
        """
        Create layout for web server.
        """

        exposure_tab = [
            dbc.CardBody(
                [
                    self.control_card,
                    self.status_card,
                ]
            )
        ]

        filename_tab = [
            self.filename_card,
            html.Div(id="filename_out"),
        ]

        detector_tab = [
            self.detector_card,
        ]

        options_tab = [
            self.options_card,
        ]

        tabs = dbc.Tabs(
            [
                dbc.Tab(exposure_tab, label="Exposure", tab_id="exposure_tab"),
                dbc.Tab(filename_tab, label="Filename", tab_id="filename_tab"),
                dbc.Tab(detector_tab, label="Detector", tab_id="detector_tab"),
                dbc.Tab(options_tab, label="Options", tab_id="options_tab"),
            ],
            id="tabs",
            active_tab="exposure_tab",
        )

        @callback(
            Output("folderselect", "value"),
            Output("rootselect", "value"),
            Output("seqnumselect", "value"),
            Input("tabs", "active_tab"),
        )
        def switch_tab(at):
            exposure = azcam.db.tools["exposure"]
            print(at)
            if at == "exposure_tab":
                return ["", "", 99]
            elif at == "filename_tab":
                seq = exposure.sequence_number
                folder = exposure.folder
                root = exposure.root
                return [folder, root, seq]
            elif at == "detector_tab":
                return ["", "", 99]
            elif at == "options_tab":
                return ["", "", 99]
            else:
                return ["", "", 99]

        # app layout
        self.app.layout = html.Div(
            [
                tabs,
                html.Div(id="hidden_div", hidden=True),
                dcc.Interval("status_interval", interval=1_000, n_intervals=0),
            ]
        )

        return

    def start(self):
        # arglist = [self.app]
        kwargs = {
            "debug": True,
            "port": "2403",
            "host": "localhost",
            "use_reloader": False,
        }
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
    webserver.app.run(debug=True, port=2403)
    # webserver.start()
    input("waiting for web server here...")
