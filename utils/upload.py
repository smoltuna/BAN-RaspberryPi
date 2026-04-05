import os
import requests
from utils.ms_graph import get_new_access_token_using_refresh_token #,is_token_expired
import json
import threading
import streamlit as st


GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"
UPLOAD_FOLDER_NAME = "App"


def upload_main(filepaths):
    access_token = get_new_access_token_using_refresh_token()
    shared_folder_location = f'/me/drive/root/{UPLOAD_FOLDER_NAME}'
    headers = {
        "Authorization": "Bearer " + access_token["access_token"]
    }
    
    # Look for UPLOAD_FOLDER_NAME in Shared folders
    items = json.loads(requests.get(GRAPH_API_ENDPOINT + "/me/drive/sharedwithme", headers=headers).text)
    found = False
    for entry in items["value"]:
        if entry["name"] == UPLOAD_FOLDER_NAME:
            found = True
            item_id = entry["remoteItem"]["id"]
            drive_id = entry["remoteItem"]["parentReference"]["driveId"]
            shared_folder_location = f"/drives/{drive_id}/items/{item_id}"
    
    # Look for UPLOAD_FOLDER_NAME in My folders
    if not found:
        items = json.loads(requests.get(GRAPH_API_ENDPOINT + '/me/drive/root/children', headers=headers).text)
        for entry in items['value']:
            if entry["name"] == UPLOAD_FOLDER_NAME:
                found = True
                item_id = entry["id"]
                drive_id = entry["parentReference"]["driveId"]
                shared_folder_location = f"/drives/{drive_id}/items/{item_id}"
    
    # UPLOAD_FOLDER_NAME does not exist, so create it in My folders
    if not found:
        body = {
            "name": UPLOAD_FOLDER_NAME,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename"
        }
        response = json.loads(requests.post(GRAPH_API_ENDPOINT + '/me/drive/root/children/', headers=headers, json=body).text)
        item_id = response["id"]
        drive_id = response["parentReference"]["driveId"]
        shared_folder_location = f"/drives/{drive_id}/items/{item_id}"

    
    # Look for files in <filepaths> that already exist in the upload folder
    files_already_existing = []
    for filepath in filepaths:
        tmp = filepath.split("/")
        dest_folder_name = f"{tmp[-3]}/{tmp[-2]}"  # "subject_id/session_name"
        file_name = os.path.basename(filepath)
        headers = {
            "Authorization": "Bearer " + access_token["access_token"]
        }
        response = requests.get(
            GRAPH_API_ENDPOINT + f"{shared_folder_location}:/{dest_folder_name}/{file_name}",
            headers=headers
        )
        if response.status_code == 200:
            files_already_existing += [filepath]

    # If files already exist display overwrite action popup
    if len(files_already_existing) > 0:
        display_existing_files_popup(files_already_existing, filepaths, access_token, shared_folder_location)
    else:
        upload(filepaths, access_token, shared_folder_location)
    

def display_existing_files_popup(files_already_existing, filepaths, access_token, shared_folder_location):
    """
    Display a pop-up window showing the files that already exist on OneDrive.

    Allows the user to choose whether to upload the files or discard them.

    Args:
    - files_already_existing (list): A list of filepaths that already exist on OneDrive.
    - filepaths (list): A list of all filepaths being checked.
    """
    st.markdown('<hr style="border: 1px solid red">', unsafe_allow_html=True)

    st.markdown("The following files already exist on Onedrive. Do you wish to overwrite them?")
    with st.markdown("\n".join([f"- {file}" for file in files_already_existing])):
        pass
    st.markdown("\n")
    with st.container():
        col1, col2, col3= st.columns([1, 1, 6])
        with col1:
            st.button(label="Upload",
                      on_click= lambda: upload(filepaths, access_token, shared_folder_location))
        with col2:
            st.button(label="Discard")
                
    st.markdown('<hr style="border: 1px solid red">', unsafe_allow_html=True)
 

def upload(filepaths, access_token, shared_folder_location):
    """
    Initiates a background thread for uploading files.

    Args:
        filepaths (list): List of file paths to be uploaded.
    """
    background_thread = threading.Thread(target=start_uploading, args=(filepaths, access_token, shared_folder_location))
    background_thread.start()
    if len(filepaths) > 0:
        return st.success("SUCCESS!", icon="✅")
    else:
        return st.warning("NO FILE TO UPLOAD", icon="⚠️")


def start_uploading(filepaths, access_token, shared_folder_location):
    """
    Uploads files one at a time.

    Args:
        filepaths (list): List of file paths to be uploaded.
    """
    for filepath in filepaths:
        single_upload(filepath, access_token, shared_folder_location)


def single_upload(filepath, access_token, shared_folder_location):
    """
    Uploads a single file.

    Args:
        filepath (str): The path of the file to be uploaded.
    """
    filepath = os.getcwd() + filepath
    file_name = os.path.basename(filepath)
    headers = {
        "Authorization": "Bearer " + access_token["access_token"]
    }
    request_body = {
        "item": {
            "description": "a large file",
            "name": file_name
        }
    }
    
    # Create a new upload session
    tmp = filepath.split("/")
    dest_folder_name = f"{tmp[-3]}/{tmp[-2]}"
    response_upload_session = requests.put(
        GRAPH_API_ENDPOINT + f"{shared_folder_location}:/{dest_folder_name}/{file_name}:/createuploadsession",
        headers=headers,
        json=request_body
    )

    try:
        upload_url = response_upload_session.json()["uploadUrl"]
    except Exception as e:
        raise Exception(str(e))
    
    # Splitting the file into chunks to avoid network truncation problems 
    # (It is not possible to upload large files in a "single available time session")
    with open(filepath, "rb") as upload:
        total_file_size = os.path.getsize(filepath)
        chunk_size = 32768000  # Adjust chunk size as needed (multiple of 32768)
        chunk_number = total_file_size // chunk_size
        chunk_leftover = total_file_size - (chunk_size * chunk_number)
        counter = 0

        while True:
            chunk_data = upload.read(chunk_size)
            start_index = counter * chunk_size
            end_index = start_index + chunk_size

            if not chunk_data:
                break
            if counter == chunk_number:
                end_index = start_index + chunk_leftover

            headers = {
                "Content-Length": f"{chunk_size}",
                "Content-Range": f"bytes {start_index}-{end_index-1}/{total_file_size}",
            }

            # Upload a chunk of data
            chunk_data_upload_status = requests.put(
                upload_url,
                headers=headers,
                data=chunk_data
            )
            
            if "createdBy" in chunk_data_upload_status.json():
                print("File upload COMPLETE")
                
            else:
                print("Upload Progression: {0}".format(chunk_data_upload_status.json()["nextExpectedRanges"]))
                counter += 1

