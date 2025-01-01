#!/bin/env python3

import json
import os
from datetime import datetime, timedelta
from typing import List

import requests
from requests.models import HTTPError

from config import (COLLECTIBLE_TYPES, COLLECTIBLES_URL, DUMP_FOLDER,
                    OUTPUT_FOLDER)


def fetch_collectibles(url: str) -> List | None:
    """Fetches latest collectibles in json format from api"""
    if not url:
        raise ValueError("URL not provided !")
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPError("Did not get status code 200 ...")
    content = response.json()
    return content


def dump_collectibles(collectibles: list) -> None:
    """Dumps all collectibles from a list to a json file"""
    if not collectibles:
        raise ValueError("Missing collectibles variable !")
    if not os.path.exists(DUMP_FOLDER):
        os.mkdir(DUMP_FOLDER)
    now = datetime.strftime(datetime.now(), format="%d_%m_%Y_%H_%M_%S")
    with open(f"{DUMP_FOLDER}collectibles_{now}.json", "w") as f:
        json.dump(collectibles, f, ensure_ascii=False, indent=4)
        print(f"Successfully dumped collectibles_{now}.json")


#def filter_types(collectibles: list, filter: list[str]) -> None | List:
#    """Filters out specific types from collectibles and prints their image URLs."""
#    collected = []
#    if not collectibles:
#        raise ValueError("Missing collectibles variable!")
#    
#    for count, collectible in enumerate(collectibles):
#        print(count)
#        collectible_type = collectible.get("type")
#
#        if collectible_type:
#            if collectible_type.lower() in filter:
#                collected.append({"id": collectible.get("id"), "image": collectible.get("image")})
#        else:
#            # If 'type' is None, check the name/description
#            name_description = f"{collectible.get('name', '')} {collectible.get('description', '')}".lower()
#            for collectible_type in filter:
#                if collectible_type.lower() in name_description:
#                    collected.append({"id": collectible.get("id"), "image": collectible.get("image")})
#    return collected



def filter_types(collectibles: list, filter: list[str]) -> list | None:
    """Filters out specific types from collectibles and collects their image URLs."""
    collected = []
    if not collectibles:
        raise ValueError("Missing collectibles variable!")
    
    for count, collectible in enumerate(collectibles):
        print(f"Processing item {count} (ID: {collectible.get('id')})")
        
        # Ensure collectible contains the necessary keys and avoid issues
        if not collectible.get("id"):
            print(f"Warning: Collectible {count} is missing 'id'. Skipping...")
            continue
        
        collectible_type = collectible.get("type")
        
        # Check if the 'type' exists and matches the filter list
        if collectible_type:
            if collectible_type.lower() in filter:
                collected.append({"id": collectible.get("id"), "image": collectible.get("image")})
        else:
            # If 'type' is None, check the name/description for the types in the filter list
            name_description = f"{collectible.get('name', '')} {collectible.get('description', '')}".lower()
            matched = False
            for collectible_type in filter:
                if collectible_type.lower() in name_description:
                    collected.append({"id": collectible.get("id"), "image": collectible.get("image")})
                    matched = True
                    break  # Break after finding the first match to avoid duplicate processing
    if not collected:
        print("No matching collectibles found.")
    
    return collected


def check_file_age(directory: str, hours: int) -> bool:
    """Checks if the most recent file in the directory is older than the specified number of hours."""
    json_files = [file for file in os.listdir(directory) if file.endswith(".json")]
    if not json_files:
        return True  # If no .json files, consider it as outdated
    json_files_with_paths = [os.path.join(directory, file) for file in json_files]
    newest_file = max(json_files_with_paths, key=os.path.getmtime)
    modified_time = os.path.getmtime(newest_file)
    modified_datetime = datetime.fromtimestamp(modified_time)
    current_time = datetime.now()
    time_diff = current_time - modified_datetime
    # Return True if the file is older than the specified number of hours
    return time_diff > timedelta(hours=hours)

def save_image(collectibles: list, output_folder: str) -> None:
    """Saves the collectible images in the specified folder."""
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)
    print(len(collectibles))
    for collectible in collectibles:
        image_name = f"{collectible.get('id').strip('collectible-')}.png"
        image_url = collectible.get("image")
        
        if image_url:
            try:
                response = requests.get(image_url)
                if response.status_code == 200:
                    image_path = os.path.join(output_folder, image_name)
                    with open(image_path, 'wb') as file:
                        file.write(response.content)
                    
                    print(f"Image saved: {image_path}")
                else:
                    print(f"Failed to download image for {collectible.get('id')}. HTTP Status Code: {response.status_code}")
            except Exception as e:
                print(f"Error downloading image for {collectible.get('id')}: {e}")
        else:
            print(f"No image URL found for {collectible.get('id')}")


def main() -> None:
    collectibles = fetch_collectibles(COLLECTIBLES_URL)
    if collectibles:
        dump_collectibles(collectibles)
        filtered_collectibles = filter_types(collectibles, COLLECTIBLE_TYPES)
        save_image(filtered_collectibles, OUTPUT_FOLDER)


if __name__ == "__main__":
    main()
