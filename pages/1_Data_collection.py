import time

import streamlit as st
from streamlit_toggle import st_toggle_switch
from datetime import datetime
import pyudev
import json

st.set_page_config(page_title="Data collection")

# -- Session state initialization -- #

if "start_data_collection" not in st.session_state:
    st.session_state.start_data_collection = False
if "connected_devices" not in st.session_state:
    st.session_state.connected_devices = []
if "session_info" not in st.session_state:
    st.session_state.session_info = json.load(open("wearable/settings/session_info.json", 'r'))


# -- Function -- #
def stop_data_collection():
    st.session_state.start_data_collection = False
    st.session_state.controller.stop_recording()


def start_data_collection():
    st.session_state.session_info = {
        "camera": enable_camera_toggle,
        "subject_id": subject_id_input,
        "session_name": session_name_input,
        "task_nr": task_number_input,
        "services": [s.lower() for s in services_input]
    }
    with open("wearable/settings/session_info.json", 'w') as f:
        f.write(json.dumps(st.session_state.session_info))
    with st.spinner("Starting recording..."):
        st.session_state.controller.start_recording()
        time.sleep(4.5)
    st.session_state.start_data_collection = True
    st.success("Data collection is started")


def get_usb_webcams():
    context = pyudev.Context()
    devices = []
    for device in context.list_devices(subsystem='video4linux'):
        if 'ID_BUS' in device and device.get('ID_BUS') == 'usb':
            device_name = device.get('ID_MODEL')
            devices.append(device_name)
    return devices


# -- variables -- #
services = [
    "Temperature",
    "Humidity",
    "Pressure",
    "Gas",
    "Color",
    "Orientation",
    "Quaternion",
    "Step_count",
    "Raw_data",
    "Heading",
    "Euler",
    "Rotation_matrix",
    "Gravity_vector",
]
session_date = str(datetime.now().strftime("%Y-%m-%d"))
# -- Front-end -- #
st.title("Data collection")
st.divider()
with st.container():
    enable_camera_toggle = st_toggle_switch(
        label="Enable camera",
        label_after=True,
        default_value=False
    )
    if enable_camera_toggle:
        usb_input_device = get_usb_webcams()
        choice = st.selectbox("Camera input", options=set(usb_input_device))

    subject_id_input = st.number_input(
        label="Subject ID",
        min_value=1,
        step=1,
        value=st.session_state.session_info['subject_id']
    )

    session_name_input = st.text_input(
        label="Session name",
        max_chars=25,
        value=st.session_state.session_info['session_name']
    )

    task_number_input = st.number_input(
        label="Task Nr.",
        min_value=st.session_state.session_info['task_nr'],
        step=1
    )

    services_input = st.multiselect("Services", options=services, default=[services[8], services[9]])
    st.divider()
    if not st.session_state.start_data_collection:
        if st.session_state.connected_devices:
            st.button(
                label="Start data collection",
                on_click=start_data_collection,
                type="primary",
                use_container_width=True
            )
        else:
            st.error("No device connected")
    else:
        st.button("Stop data collection", on_click=stop_data_collection, type="primary", use_container_width=True)
