import time
import streamlit as st
import os
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go

# Use the full page instead of a narrow central column
st.set_page_config(layout="wide")

# Session state initialization
if "start_data_collection" not in st.session_state:
    st.session_state.start_data_collection = False
if "connected_devices" not in st.session_state:
    st.session_state.connected_devices = []
if "session_info" not in st.session_state:
    st.session_state.session_info = json.load(open("wearable/settings/session_info.json", 'r'))
if "session_is_reloaded" not in st.session_state:
    st.session_state.session_is_reloaded = True
if "device_names" not in st.session_state:
    st.session_state.device_names = {}

state = st.session_state

# General path to live data
PATH_TO_LIVE_DATA = os.path.join(
    os.getcwd(),
    f"wearable/recordings/{state.session_info['subject_id']}/{state.session_info['session_name']}"
)


# ========= PLOT FUNCTIONS ============== #
def plot_raw_data(df, thingy):
    fig_acc = go.Figure()
    fig_gyro = go.Figure()
    fig_comp = go.Figure()

    # Accelerometer graph
    trace_x_acc = go.Scatter(x=df['gen_time'], y=df['acc_x'], mode='lines', name='x', line=dict(color='#ff8c00'))
    trace_y_acc = go.Scatter(x=df['gen_time'], y=df['acc_y'], mode='lines', name='y', line=dict(color='purple'))
    trace_z_acc = go.Scatter(x=df['gen_time'], y=df['acc_z'], mode='lines', name='z', line=dict(color='#008080'))

    fig_acc.add_trace(trace_x_acc)
    fig_acc.add_trace(trace_y_acc)
    fig_acc.add_trace(trace_z_acc)
    fig_acc.update_layout({'title': f'{dev_name} accelerometer data', 'width': 350})
    fig_acc.update_layout(legend=dict(orientation="h"))

    # Gyroscope graph
    trace_x_gyro = go.Scatter(x=df['gen_time'], y=df['gyro_x'], mode='lines', name='x', line=dict(color='#ff8c00'))
    trace_y_gyro = go.Scatter(x=df['gen_time'], y=df['gyro_y'], mode='lines', name='y', line=dict(color='purple'))
    trace_z_gyro = go.Scatter(x=df['gen_time'], y=df['gyro_z'], mode='lines', name='z', line=dict(color='#008080'))

    fig_gyro.add_trace(trace_x_gyro)
    fig_gyro.add_trace(trace_y_gyro)
    fig_gyro.add_trace(trace_z_gyro)
    fig_gyro.update_layout({'title': f'{dev_name} Gyroscope data', 'width': 350})
    fig_gyro.update_layout(legend=dict(orientation="h"))

    # Compass graph
    trace_x_comp = go.Scatter(x=df['gen_time'], y=df['comp_x'], mode='lines', fill='tozeroy', name='x',
                              line=dict(color='#ff8c00'))
    trace_y_comp = go.Scatter(x=df['gen_time'], y=df['comp_y'], mode='lines', fill='tonexty', name='y',
                              line=dict(color='purple'))
    trace_z_comp = go.Scatter(x=df['gen_time'], y=df['comp_z'], mode='lines', fill='tonexty', name='z',
                              line=dict(color='#008080'))

    fig_comp.add_trace(trace_x_comp)
    fig_comp.add_trace(trace_y_comp)
    fig_comp.add_trace(trace_z_comp)
    fig_comp.update_layout({'title': f'{thingy} Compass data', 'width': 350})
    fig_comp.update_layout(legend=dict(orientation="h"))

    return [fig_acc, fig_gyro, fig_comp]


def plot_euler_data(df, thingy):
    fig = go.Figure()
    trace_x = go.Scatter(x=df['gen_time'], y=df['x'], mode='lines', name='x', line=dict(color='#ff8c00'))
    trace_y = go.Scatter(x=df['gen_time'], y=df['y'], mode='lines', name='y', line=dict(color='purple'))
    trace_z = go.Scatter(x=df['gen_time'], y=df['z'], mode='lines', name='z', line=dict(color='#008080'))
    fig.add_trace(trace_x)
    fig.add_trace(trace_y)
    fig.add_trace(trace_z)

    return fig


# ========= FETCH DATA FUNCTIONS ============== #
def fetch_raw_data(device):
    col_names = ['time', 'gen_time', 'acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z', 'comp_x', 'comp_y',
                 'comp_z']
    path = f"{PATH_TO_LIVE_DATA}/{device}_raw_data_{str(state.session_info['task_nr'])}.csv"

    data_to_plot = pd.read_csv(
        path,
        parse_dates=True,
        names=col_names,
    )
    if len(data_to_plot) > 640:
        data_to_plot = data_to_plot.tail(640)

    return data_to_plot


def fetch_euler_data(device):
    col_names = ['rec_time', 'gen_time', 'x', 'y', 'z']
    path = f"{PATH_TO_LIVE_DATA}/{device}_euler_{str(state.session_info['task_nr'])}.csv"
    data_to_plot = pd.read_csv(
        path,
        parse_dates=True,
        names=col_names
    )
    if len(data_to_plot) > 640:
        data_to_plot = data_to_plot.tail(640)

    return data_to_plot


# ========= FRONT END ============== #
st.title("Analytics")

with st.container():

    # if sensors are recording then plot live data
    if st.session_state.start_data_collection:
        st.markdown("## Real Time Data")
        data_to_display = st.selectbox(
            label="Data to display",
            options=st.session_state.session_info["services"],
            index=st.session_state.session_info["services"].index("raw_data")
        )

        if data_to_display == 'raw_data':
            dfs = {}
            placeholders = []

            # For loop for placeholders (rows) creation
            for dev in st.session_state.device_names.values():
                placeholders.append(st.empty())
                dfs[dev] = fetch_raw_data(dev)

            # While loop for data plotting
            while st.session_state.start_data_collection:
                i = 0
                for dev in st.session_state.connected_devices:
                    dev_name = st.session_state.device_names[dev.addr]
                    dfs[dev_name] = fetch_raw_data(dev_name)

                    with placeholders[i].container():
                        charts = plot_raw_data(dfs[dev_name], dev_name)
                        col1, col2, col3 = st.columns([0.33, 0.33, 0.33])  # dividing a row into three equal columns
                        with col1:
                            st.plotly_chart(charts[0])  # display accelerometer data graph
                        with col2:
                            st.plotly_chart(charts[1])  # display gyroscope data graph
                        with col3:
                            st.plotly_chart(charts[2])  # display compass data graph
                    i = i + 1

                # time.sleep(0.2)

        elif data_to_display == 'euler':
            dfs = {}
            placeholders = []

            # For loop for placeholders (rows) creation
            for dev in st.session_state.device_names.values():
                placeholders.append(st.empty())
                dfs[dev] = fetch_euler_data(dev)

            # While loop for data plotting
            while st.session_state.start_data_collection:
                i = 0
                for dev in st.session_state.connected_devices:
                    dev_name = st.session_state.device_names[dev.addr]
                    dfs[dev_name] = fetch_euler_data(dev_name)
                    with placeholders[i].container():
                        chart = plot_euler_data(dfs[dev_name], dev_name)
                        st.plotly_chart(chart)  # display euler data graph
                    i = i + 1

    else:

        for dev in st.session_state.connected_devices:
            dev_name = dev.getValueText(9)
            with open(f"{PATH_TO_LIVE_DATA}/{dev_name}_raw_data_{str(state.session_info['task_nr'])}.csv",
                      "rb") as file:
                btn = st.download_button(
                    label=f"Download {dev_name} csv",
                    data=file,
                    file_name=f"{PATH_TO_LIVE_DATA}/{dev_name}_raw_data_{str(state.session_info['task_nr'])}.csv",
                    mime="text/csv"
                )
