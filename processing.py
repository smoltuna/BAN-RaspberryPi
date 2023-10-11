import argparse
import glob
import os
import json

import pandas as pd
import numpy as np

from constants import WEARABLE_POSITIONS, HUMAN_PARTS, WEARABLE_COLUMNS


def get_hpe_columns():
    human_columns = ["timestamp", "frame_id", "body_id"]
    for kp_name in HUMAN_PARTS:
        for coord in ["x", "y", "z"]:
            human_columns.append(kp_name + "_" + coord)
    return human_columns


def get_wearable_columns():
    wearable_columns = ["timestamp", "frame_id"]
    for wearable_pos in WEARABLE_POSITIONS:
        for wearable_col in WEARABLE_COLUMNS:
            wearable_columns.append(wearable_pos + "_" + wearable_col)
    return wearable_columns


def merge(camera_df, wearable_data, output_fn_prefix):
    fps_to_ms_15 = (1e9 / 15) / 2

    print("Merging process ... ")
    merge_data = pd.DataFrame()
    for index, skeleton in camera_df.iterrows():
        curr_time = skeleton["timestamp"]

        # Get the current time wearable data
        curr_time_wearable_data = {}
        for wearable_pos in wearable_data:
            curr_time_wearable_data[wearable_pos] = wearable_data[wearable_pos].loc[
                (curr_time - fps_to_ms_15 <= wearable_data[wearable_pos]["timestamp"]) &
                (wearable_data[wearable_pos]["timestamp"] <= curr_time + fps_to_ms_15)
                ].reset_index(drop=True)

        # Add empty rows to normalize wearable data
        curr_time_count = max([len(curr_time_wearable_data[w].index) for w in curr_time_wearable_data])
        for wearable_pos in curr_time_wearable_data:
            curr_time_wearable_data[wearable_pos] = curr_time_wearable_data[wearable_pos].reindex(
                list(range(0, curr_time_count)))
            curr_time_wearable_data[wearable_pos] = curr_time_wearable_data[wearable_pos].rename(
                columns=dict(zip(
                    curr_time_wearable_data[wearable_pos].columns,
                    [(wearable_pos + "_" + col) for col in curr_time_wearable_data[wearable_pos].columns]
                ))
            )

        # Concat all data
        curr_time_skeleton = pd.DataFrame(
            [skeleton.values] * curr_time_count, columns=camera_df.columns)
        curr_time_merge = curr_time_skeleton
        for wearable_pos in curr_time_wearable_data:
            curr_time_merge = pd.concat(
                [curr_time_merge, curr_time_wearable_data[wearable_pos]], axis=1)

        merge_data = pd.concat([merge_data, curr_time_merge], ignore_index=True)
        print(index)
    print("Merging process ... finished")

    print("Saving the whole data merged")
    merge_data.to_csv(output_fn_prefix + "_merge.csv")
    print("Saving the camera data merged")
    merge_camera_data = merge_data[get_hpe_columns()].drop_duplicates().reset_index(drop=True)
    merge_camera_data.to_csv(output_fn_prefix + "_merge_camera.csv")
    print("Saving the wearable data merged")
    merge_wearable_data = merge_data[get_wearable_columns()].drop_duplicates().reset_index(drop=True)
    merge_wearable_data.to_csv(output_fn_prefix + "_merge_wearable.csv")
    print("Saving data ... finished")


def main(camera_fp, wearable_fp):
    human_columns = get_hpe_columns()

    # Camera file: 
    preprocessed_camera_data = os.path.splitext(os.path.split(camera_fp)[-1])[0] + "_preprocessed.csv"
    if not os.path.exists(preprocessed_camera_data):
        print("Reading camera data: ")
        with open(camera_fp, "r") as f:
            camera_data = json.load(f)
        print(" - length: {}".format(len(camera_data)))
        camera_df = pd.DataFrame(columns=human_columns)
        for scene in camera_data:
            timestamp = int(scene["timestamp"] * 1e6)  # to nanoseconds
            frame_id = scene["frame_id"]
            multip_kp3d = scene["kp3d"]

            scene_list = []
            body_id = 0
            for person in multip_kp3d:
                person_list = [timestamp, frame_id, body_id]
                for kp_name in HUMAN_PARTS:
                    person_list.extend(person[kp_name][0:3] if kp_name in person else [np.nan, np.nan, np.nan])
                scene_list.append(person_list)
                body_id += 1

            camera_df = pd.concat([camera_df, pd.DataFrame(scene_list, columns=human_columns)], ignore_index=True)
        camera_df.to_csv(preprocessed_camera_data)
    else:
        print("Reading preprocessed camera data: ")
        camera_df = pd.read_csv(preprocessed_camera_data, index_col=0)
    min_timestamp = camera_df["timestamp"].min()
    max_timestamp = camera_df["timestamp"].max()
    print(" - camera: length: {}, timestamp_min: {} ms, timestamp_max: {} ms".format(
        len(camera_df.index), min_timestamp * 1e-6, max_timestamp * 1e-6))

    # Wearable files: 
    print("Reading wearable data: ")
    wearable_data = {}
    for wearable_pos in WEARABLE_POSITIONS:
        fp = glob.glob(os.path.join(wearable_fp, wearable_pos + "_raw_data_*.csv"))[0]
        wearable_csv = pd.read_csv(fp, names=WEARABLE_COLUMNS, parse_dates=["timestamp"])
        wearable_csv["timestamp"] = wearable_csv["timestamp"].dt.tz_localize("Europe/Rome").astype(np.int64)
        wearable_csv = wearable_csv.loc[
            (wearable_csv["timestamp"] > min_timestamp) &
            (wearable_csv["timestamp"] < max_timestamp)]

        wearable_data[wearable_pos] = wearable_csv
        print(" - {}: length: {}, min_timestamp: {} ms, max_timestamp: {} ms".format(
            wearable_pos, len(wearable_csv.index),
            wearable_csv["timestamp"].min() * 1e-6,
            wearable_csv["timestamp"].max() * 1e-6))

        if wearable_csv["timestamp"].min() < min_timestamp:
            print("Error: wearable min timestamp under limit")
        if wearable_csv["timestamp"].max() > max_timestamp:
            print("Error: wearable max timestamp over limit")

    merge(camera_df, wearable_data, os.path.splitext(os.path.split(camera_fp)[-1])[0])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Wearable and Camera preprocessing",
        epilog="Mirco De Marchi & Cristian Turetta")
    parser.add_argument("--camera",
                        "-c",
                        dest="camera",
                        required=True,
                        help="file path to the keypoints sequence file")
    parser.add_argument("--wearable",
                        "-w",
                        dest="wearable",
                        required=True,
                        help="folder path to the wearable sequence file")
    args = parser.parse_args()
    main(args.camera, args.wearable)
