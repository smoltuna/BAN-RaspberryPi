import os
import time
import streamlit as st
from wearable.controller import Controller
import uuid
import subprocess


# Function to kill process on page reload
def handle_page_reload():
    try:
        cmd = "ps -ef | grep bluepy-helper"
        output = subprocess.check_output(["bash", "-c", cmd])

        output = output.decode().strip().split('\n')
        output = [str(line).split(' ') for line in output if 'bluepy/bluepy-helper' in line]

        if output:
            # Kill each sensor's thread
            i = 0
            for line in output:
                for item in line:
                    if item == '':
                        line.remove(item)
                os.system(f'kill {line[1]}')
    except Exception as e:
        print(e.args)


# session state initialization
if "session_is_reloaded" not in st.session_state:
    st.session_state.session_is_reloaded = True
if "start_discovery" not in st.session_state:
    st.session_state.start_discovery = False
if "connected_devices" not in st.session_state:
    st.session_state.connected_devices = []
if "discovered_devices" not in st.session_state:
    st.session_state.discovered_devices = []
if "device_names" not in st.session_state:
    st.session_state.device_names = {}
if "controller" not in st.session_state:
    st.session_state.controller = Controller()
if "disconnect_all" not in st.session_state:
    st.session_state.disconnect_all = False
if "rows_discovered_devices" not in st.session_state:
    st.session_state.rows_discovered_devices = []
if "rows_connected_devices" not in st.session_state:
    st.session_state.rows_connected_devices = []
if "start_data_collection" not in st.session_state:
    st.session_state.start_data_collection = False
if "active_threads" not in st.session_state:
    st.session_state.active_threads = []
if "name_changed" not in st.session_state:
    st.session_state.name_changed = True

if st.session_state.session_is_reloaded:
    handle_page_reload()


# Function to erase content of an object
def empty(obj):
    obj.empty()


# --- Functions to generate discovered list --- #

def add_row_discovered_list():
    element_id = uuid.uuid4()
    st.session_state.rows_discovered_devices.append(str(element_id))


def connect_dev(row_id, device):
    device_name = device.getValueText(9)
    if device not in st.session_state.connected_devices and st.session_state.controller.connect(device, device_name):
        st.session_state.device_names[device.addr] = device_name
        st.session_state.rows_discovered_devices.remove(str(row_id))
        st.session_state.discovered_devices.remove(device)
        st.session_state.connected_devices.append(device)
        add_row_connected_list()
        if device_name is not None:
            msg = st.success(f"{device_name} is now connected")
        else:
            msg = st.success(f"{device.addr} is now connected")
        time.sleep(1)
        msg.empty()

    elif device in st.session_state.connected_devices:
        msg = st.info("Device already connected")
        time.sleep(2)
        msg.empty()
    else:
        if device_name is not None:
            msg = st.error(f"Can't connect to {device_name}")
            time.sleep(2)
            msg.empty()
        else:
            msg = st.error(f"Can't connect to {device.addr}")
            time.sleep(2)
            msg.empty()


def generate_row_discovered_list(row_id, device):
    device_name = device.getValueText(9)
    row_container = st.empty()
    row_columns = row_container.columns([8, 2])
    if device_name is not None:
        row_columns[0].write(f"Device: {device_name}")
    else:
        row_columns[0].write(f"Device: {device.addr}")

    row_columns[1].button("Connect", key=f"connect-{row_id}", on_click=connect_dev, args=[row_id, device])


# --- Functions to generate connected devices list --- #

def add_row_connected_list():
    element_id = uuid.uuid4()
    st.session_state.rows_connected_devices.append(str(element_id))


def remove_row_connected_list(row_id, device):
    st.session_state.rows_connected_devices.remove(str(row_id))
    st.session_state.connected_devices.remove(device)
    st.session_state.controller.disconnect_device(device.addr)


def remove_rows_connected_list():
    st.session_state.rows_connected_devices = []


def generate_row_connected_list(row_id, device):
    device_name = device.getValueText(9)
    battery = st.session_state.controller.get_battery(device.addr)[0]
    row_container = st.empty()
    row_columns = row_container.columns([3, 2, 2])
    row_columns[0].markdown(f"**:green[{device_name} is connected]**")
    row_columns[1].markdown(f"**:green[{battery}%]**")
    row_columns[2].button(
        "Disconnect",
        key=f"disconnect-{device.addr}",
        on_click=remove_row_connected_list,
        args=[row_id, device]
    )


# --- Disconnect all devices --- #

def disconnect_all():
    while st.session_state.disconnect_all:
        for dev in st.session_state.connected_devices:
            st.session_state.controller.disconnect_device(dev.addr)
            st.session_state.connected_devices.remove(dev)
        if not st.session_state.connected_devices:
            st.session_state.disconnect_all = False


# --- Start discover ---#

def start_discovery():
    with st.spinner("Scan for devices..."):
        st.session_state.discovered_devices = st.session_state.controller.discovery_devices()
    for d in st.session_state.discovered_devices:
        add_row_discovered_list()
    st.session_state.start_discovery = True


# --- Front end --- #

# Home page title
st.title("IoT4Care Dashboard")
st.divider()
if st.session_state.start_discovery:
    st.markdown("## Discovered devices")
start_discovery_container = st.container()
st.session_state.session_is_reloaded = False
with start_discovery_container:
    main_btn = st.button("Start discovery", type="primary", on_click=start_discovery)

# List loop
for row, device in zip(st.session_state.rows_discovered_devices, st.session_state.discovered_devices):
    generate_row_discovered_list(row, device)

st.divider()
st.markdown("## Connected devices")
if not st.session_state.connected_devices:
    st.error("No device connected")
second_container = st.empty()

# if st.session_state.name_changed:
#     empty(second_container)
#     remove_rows_connected_list()
#     with second_container.container():
#         for row, device in zip(st.session_state.rows_connected_devices, st.session_state.connected_devices):
#             generate_row_connected_list(row, device)
#     st.session_state.name_changed = False
with second_container.container():
    for row, device in zip(st.session_state.rows_connected_devices, st.session_state.connected_devices):
        generate_row_connected_list(row, device)

with st.container():
    if st.button("Disconnect all", use_container_width=True, type="primary"):
        st.session_state.disconnect_all = True
        if not st.session_state.connected_devices:
            message = st.error("There is not connected device")
            time.sleep(2)
            message.empty()
        disconnect_all()
        if not st.session_state.connected_devices:
            message = st.info("All devices are disconnected")
            time.sleep(2)
            message.empty()
        empty(second_container)
