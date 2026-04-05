import os
import streamlit as st
from utils.upload import upload_main
import json


st.set_page_config(page_title="Upload OneDrive")

# -- Session state initialization -- #
if "session_info" not in st.session_state:
    st.session_state.session_info = json.load(open("wearable/settings/session_info.json", 'r'))


def search_files():
    """
    Search for files in the specified directory based on subject_id_input and session_name_input.

    Returns:
        list: List of file paths.
    """
    all_files = []

    if not os.path.exists(f"wearable/recordings/{subject_id_input}"):
        return []

    if session_name_input == "":
        path = os.path.join(
            os.getcwd(),
            f"wearable/recordings/{subject_id_input}"
        )

        # Generate a list of relative paths for all files in the directory and its subdirectories.
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join("/wearable/recordings/" + str(subject_id_input), os.path.relpath(os.path.join(root, file), path))
                all_files.append(file_path)

        return all_files

    if os.path.exists(f"wearable/recordings/{subject_id_input}/{session_name_input}"):
        path = os.path.join(
            os.getcwd(),
            f"wearable/recordings/{subject_id_input}/{session_name_input}"
        )
        return [f"/wearable/recordings/{subject_id_input}/{session_name_input}/{nameFile}" for nameFile in os.listdir(path)]
    else:
        return []


def get_subdirectories(path):
    """
    Get subdirectories in the specified path.

    Args:
        path (str): Path to search for subdirectories.

    Returns:
        list: List of subdirectories.
    """
    if os.path.exists(path):
        return [""] + [d for d in os.listdir(f"wearable/recordings/{subject_id_input}")]
    return []

# -- Front-end -- #
  
# Streamlit title and container
st.title("Upload to OneDrive")
st.divider()
with st.container():
    # Streamlit input fields
    subject_id_input = st.number_input(
        label="Subject ID",
        min_value=1,
        step=1,
        value=st.session_state.session_info['subject_id']
    )
    
    session_name_input = st.selectbox(
        "Session name (Optional)",
        get_subdirectories(f"wearable/recordings/{subject_id_input}"),
        index=0,
    )

    # Search for files and create a multiselect widget
    files_in_directory = search_files()
    selected_files = st.multiselect("Select files", files_in_directory)
    
    # Upload button
    if st.button(
        label="Upload",
        on_click=lambda: upload_main(selected_files),
        type="primary",
        use_container_width=True
    ):
        if len(selected_files) > 0:
            st.info("Files uploading:\n" + "\n".join([f"- {file}" for file in selected_files]), icon="ℹ️")
