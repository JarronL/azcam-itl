import numpy as np
from matplotlib import pyplot as plt
from nicegui import ui
from nicegui.events import KeyEventArguments

#from nicegui import app, ui

#app.add_static_files('/mystatic', 'mystatic')
#app.add_static_files('/static', 'mystatic')

#with ui.card().tight() as card:

count = 0
sequence_count = 1
image_type_name = 'Zero'
image_types = {1: 'Zero', 2: 'Object', 3: 'Flat', 4: 'Dark'}

def expose(value):
    print(value,"exposing")

def update_sequence_count():
    global sequence_count
    sequence_count = seq_count_control.value
    sequence_badge.text = int(sequence_count)

def update_image_type():
    exposure_badge.text =  image_types[image_type.value]

def update():
    global count
    count += 1
    #print("updating")
    dewtemp.text=f"{count}"
    camtemp.text=f"{2*count}"
    messages.text = f'some messages...{count}...'

with ui.tabs() as tabs:
    ui.tab('Home', icon='home')
    ui.tab('Help', icon='help')

ui.timer(interval=1.0, callback=update)

with ui.tab_panels(tabs, value='Home'):
    with ui.tab_panel('Home'):

        with ui.row() as row1:
            with ui.column() as col1:
                with ui.button('Expose', on_click=lambda: expose(f'Exposure started')).tooltip('Click to start a new exposure').style("width:8em"):
                    exposure_badge = ui.badge(f"{image_type_name}", color='red').props('floating')

                with ui.button('Sequence', on_click=lambda: ui.notify(f'Sequence started')).style("width:8em"):
                    sequence_badge = ui.badge(f"{sequence_count}", color='red').props('floating')

                ui.button('Filename', on_click=lambda: ui.notify(f'You clicked me!')).style("width:8em")
                ui.button('Detector', on_click=lambda: ui.notify(f'You clicked me!')).style("width:8em")
                ui.button('Reset', on_click=lambda: ui.notify(f'You clicked me!')).style("width:8em")
                ui.button('Abort', on_click=lambda: ui.notify(f'You clicked me!')).style("width:8em")
                ui.button('Preferences', on_click=lambda: ui.notify(f'You clicked me!')).style("width:8em")

            with ui.column() as col2:
                with ui.row():
                        image_type = ui.select(image_types,value=1,on_change=lambda: update_image_type()).tooltip("Exposure type")
                        seq_count_control = ui.number(label='Num Seq.', value=1, format='%d', on_change=lambda: update_sequence_count()).style("width:5em").tooltip("Number of exposures in Sequence")
                        checkbox = ui.checkbox('Test Image').tooltip("Check for a test exposure")
                        ui.number(label='Exposure Time', value=1.0, format='%.3f',
                                on_change=lambda e: exposure_time.set_text(f'Exposure time will be: {e.value}')).tooltip("Exposure time in seconds")
                        exposure_time = ui.label()

                with ui.row():
                        ui.input(label='Image Title', placeholder='start typing',
                                validation={'Input too long': lambda value: len(value) < 120}).style("width:30em").tooltip("Image title - OBJECT keyword")


                with ui.row():
                     camtemp_label = ui.label("CamTemp").style('font-weight:bold')
                     camtemp = ui.label("camtemp").style('border:solid 1pt; width: 5em; background:lightcyan').tooltip("sensor temperature in Celsius")
                     dewtemp_label = ui.label("DewTemp").style('font-weight:bold')
                     dewtemp = ui.label("dewtemp").style('border:solid 1pt; width: 5em; background:lightcyan').tooltip("dewar temperature in Celsius")
                     ui.label("Seq. Count").style('font-weight:bold')
                     ui.label('1').style('border:solid 1pt; width: 5em; background:lightcyan').tooltip("current sequence count")
                
            with ui.card():
                with ui.row():
                    #messages = ui.label('Messages...').style('border:solid 1pt; background:lightcyan; width: 30em')
                    messages = ui.label('Messages...').tailwind("font-bold")
                with ui.row():
                    ui.label('Progress').tailwind("font-bold")
                    ui.linear_progress().style("width:20em").value=0.75

    with ui.tab_panel('Help'):
        ui.markdown('''This is **Markdown** help.''')

def handle_key(e: KeyEventArguments):
    if e.key == 'f' and not e.action.repeat:
        if e.action.keyup:
            ui.notify('f was just released')
        elif e.action.keydown:
            ui.notify('f was just pressed')
    if e.modifiers.shift and e.action.keydown:
        if e.key.arrow_left:
            ui.notify('going left')
        elif e.key.arrow_right:
            ui.notify('going right')
        elif e.key.arrow_up:
            ui.notify('going up')
        elif e.key.arrow_down:
            ui.notify('going down')

# keyboard = ui.keyboard(on_key=handle_key)
# ui.label('Key events can be caught globally by using the keyboard element.')
# ui.checkbox('Track key events').bind_value_to(keyboard, 'active')


"""
ui.upload(on_upload=lambda e: ui.notify(f'Uploaded {e.name}')).classes('max-w-full')

with ui.pyplot(figsize=(3, 2)):
    x = np.linspace(0.0, 5.0)
    y = np.cos(2 * np.pi * x) * np.exp(-x)
    plt.plot(x, y, '-')

slider = ui.slider(min=0, max=1, step=0.01, value=0.5)
ui.circular_progress().bind_value_from(slider, 'value')


#ui.image('https://picsum.photos/id/377/640/360')
"""


ui.run(title="AzCam Exposure Control", port=8899)