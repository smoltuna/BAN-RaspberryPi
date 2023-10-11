import json
import time
import streamlit as st
import os
import json

# default settings
default_settings: dict = json.load(open(os.path.join(os.getcwd(), 'wearable/settings/config.json')))

# session state initialization
if "start_discovery" not in st.session_state:
    st.session_state.start_discovery = False
if "connected_devices" not in st.session_state:
    st.session_state.connected_devices = []
if "discovered_devices" not in st.session_state:
    st.session_state.discovered_devices = []
if "custom_settings" not in st.session_state:
    st.session_state.custom_setting = {}
if "current_settings" not in st.session_state:
    st.session_state.current_settings = default_settings
if "device_names" not in st.session_state:
    st.session_state.device_names = {}
if "name_changed" not in st.session_state:
    st.session_state.name_changed = True


# custom settings
st.title("Set connection, environment, motion settings of your sensors")
with st.container():
    with st.form("device_name_form"):
        st.markdown("## Device name")
        row = st.columns(2)
        with row[0]:
            op = [dev.addr for dev in st.session_state.connected_devices]
            thingy = st.selectbox(
                label="Select the device",
                options=op
            )

            for d in st.session_state.connected_devices:
                if d.addr == thingy:
                    device = d

        dev_name = st.text_input(
            label="Device name",
            placeholder="Thingy",
            max_chars=10
        )

        if st.form_submit_button("Set device name"):
            st.session_state.controller.set_dev_name(dev_name, device)
            st.session_state.device_names[device.addr] = dev_name
            st.session_state.name_changed = True
    with st.form(key="settings_form"):
        # connection settings
        with st.container():
            st.markdown("## Connection settings")
            adv_int_input = st.number_input(
                label="Adv interval (32 - 8000)",
                value=st.session_state.current_settings["adv_interval"],
                min_value=32,
                max_value=8000,
                step=1
            )
            adv_timeout_input = st.number_input(
                label="Adv timout (0 -180)",
                value=st.session_state.current_settings["adv_timeout"],
                min_value=0,
                max_value=180,
                step=1
            )
            min_conn_int_input = st.number_input(
                label="Min connection interval (6 - 3200)",
                value=st.session_state.current_settings["min_conn_interval"],
                min_value=6,
                max_value=3200,
                step=1
            )
            max_conn_int_input = st.number_input(
                label="Max connection interval (6 - 3200)",
                value=st.session_state.current_settings["max_conn_interval"],
                min_value=6,
                max_value=3200,
                step=1
            )
            slave_latency_input = st.number_input(
                label="Slave latency (0 - 500)",
                value=st.session_state.current_settings["slave_latency"],
                min_value=0,
                max_value=500,
                step=1
            )

            conn_sup_timeout_input = st.number_input(
                label="Supervision timeout (10 - 32)",
                value=st.session_state.current_settings["conn_sup_timeout"],
                min_value=10,
                max_value=3200,
                step=1
            )

        st.divider()
        # environment settings
        with st.container():
            st.markdown("## Environment settings")
            temp_int_input = st.number_input(
                label="Temperature interval in ms (100 - 60000)",
                value=st.session_state.current_settings["temp_int"],
                min_value=100,
                max_value=60000,
                step=1
            )
            pressure_int_input = st.number_input(
                label="Pressure interval in ms (50 - 60000)",
                value=st.session_state.current_settings["press_int"],
                min_value=50,
                max_value=60000,
                step=1
            )
            humidity_int_input = st.number_input(
                label="Humidity interval in ms (100- 60000)",
                value=st.session_state.current_settings["humid_int"],
                min_value=100,
                max_value=60000,
                step=1
            )

            color_int_input = st.number_input(
                label="Color interval in ms (200 - 60000)",
                value=st.session_state.current_settings["color_int"],
                min_value=200,
                max_value=60000,
                step=1
            )

            gas_mode_input = st.radio(
                label="Gas mode",
                options=("1s interval", "10s interval", "60s interval"),
                index=st.session_state.current_settings["gas_mode_int"]
            )

        st.divider()
        # motion settings
        with st.container():
            st.markdown("## Motion settings")
            step_counter_input = st.number_input(
                label="Step counter interval in ms (100 - 5000)",
                value=st.session_state.current_settings["step_int"],
                min_value=100,
                max_value=5000,
                step=1
            )
            temp_comp_int_input = st.number_input(
                label="Temperature compensation interval in ms (100 - 5000)",
                value=st.session_state.current_settings["temp_comp"],
                min_value=100,
                max_value=5000,
                step=1
            )
            magnet_comp_int_input = st.number_input(
                label="Magnetometer compensation interval in ms (100 - 1000)",
                value=st.session_state.current_settings["magnet_comp_int"],
                min_value=100,
                max_value=1000,
                step=1
            )
            motion_freq_input = st.slider(
                label="Motion sampling frequency in Hz (5 - 200)",
                value=st.session_state.current_settings["sampling_frequency"],
                min_value=5,
                max_value=200,
                step=1
            )

        st.divider()
        submit = st.form_submit_button("Set configuration")
        if submit and st.session_state.connected_devices:

            st.session_state.custom_settings = {
                "transmission_mode": "False",
                "fall_time_window_for_detection": 2,
                "shake_time_window_for_detection": 2,

                "adv_interval": adv_int_input,
                "adv_timeout": adv_timeout_input,

                "min_conn_interval": min_conn_int_input,
                "max_conn_interval": max_conn_int_input,
                "slave_latency": slave_latency_input,
                "conn_sup_timeout": conn_sup_timeout_input,

                "temp_int": temp_int_input,
                "press_int": pressure_int_input,
                "humid_int": humidity_int_input,
                "gas_mode_int": gas_mode_input,
                "color_int": color_int_input,

                "step_int": step_counter_input,
                "temp_comp": temp_comp_int_input,
                "sampling_frequency": motion_freq_input,
                "magnet_comp_int": magnet_comp_int_input,

                "speaker_mode": "0x03",
                "microphone_mode": "0x01"
            }
            st.session_state.current_settings = st.session_state.custom_settings
            with open("wearable/settings/config.json", 'w') as f:
                f.write(json.dumps(st.session_state.current_settings))
            st.session_state.controller.set_conf()
            st.success("Sensors are configured correctly")
        elif not st.session_state.connected_devices:
            st.error("No device connected")
