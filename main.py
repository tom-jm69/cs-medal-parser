#!/bin/env python3

import json
import os
import re
from datetime import datetime
from io import BytesIO
from typing import List

import requests
from PIL import Image
from requests.models import HTTPError

from config import COLLECTIBLE_TYPES, COLLECTIBLES_URL, DUMP_FOLDER, OUTPUT_FOLDER


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


# def filter_types(collectibles: list, filter: list[str]) -> None | List:
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

    # Create a regex pattern that matches any of the words in the filter list
    filter_pattern = r"(?i)\b(?:{}|{})\b".format(
        "|".join(map(re.escape, filter)),  # Exact matches for the filter
        "|".join(
            [re.escape(f" {term} ") for term in filter]
        ),  # Ensure space-separated terms match
    )

    for count, collectible in enumerate(collectibles):
        print(f"Processing item {count} (ID: {collectible.get('id')})")

        # Ensure collectible contains the necessary keys and avoid issues
        if not collectible.get("id"):
            print(f"Warning: Collectible {count} is missing 'id'. Skipping...")
            continue

        collectible_type = collectible.get("type")

        # Check if the 'type' exists and matches the filter list
        if collectible_type:
            if re.search(filter_pattern, collectible_type.lower()):
                collected.append(
                    {"id": collectible.get("id"), "image": collectible.get("image")}
                )
        else:
            # If 'type' is None, check the name/description for the types in the filter list using regex
            name_description = f"{collectible.get('name', '')} {collectible.get('description', '')}".lower()
            if re.search(filter_pattern, name_description):
                collected.append(
                    {"id": collectible.get("id"), "image": collectible.get("image")}
                )

    if not collected:
        print("No matching collectibles found.")

    return collected


def save_image(collectibles: list, output_folder: str) -> None:
    """Saves the collectible images in the specified folder, resizing them to 256x192 without losing content."""
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    for collectible in collectibles:
        image_name = f"{collectible.get('id').strip('collectible-')}.png"
        image_url = collectible.get("image")
        image_path = os.path.join(output_folder, image_name)

        if image_url:
            try:
                # If the image already exists, check if it matches the required resolution
                if os.path.exists(image_path):
                    with Image.open(image_path) as img:
                        if img.size != (256, 192):
                            print(f"Resizing image {image_name} to 256x192...")
                            img = resize_and_pad_image(img)
                            img.save(image_path)
                            print(f"Image resized and saved: {image_path}")
                        else:
                            print(f"Image {image_name} already has the correct resolution.")
                else:
                    # If the image does not exist, download and resize it
                    print(f"Downloading image {image_name}...")
                    response = requests.get(image_url)
                    img = Image.open(BytesIO(response.content))

                    # Resize and pad the image to 256x192
                    img = resize_and_pad_image(img)
                    img.save(image_path)
                    print(f"Image saved: {image_path}")
            except Exception as e:
                print(f"Error downloading or processing image for {collectible.get('id')}: {e}")
        else:
            print(f"No image URL found for {collectible.get('id')}")

def resize_and_pad_image(img: Image) -> Image:
    """Resizes the image while maintaining aspect ratio and pads it to 256x192."""
    # Resize while maintaining aspect ratio
    img.thumbnail((256, 192), Image.Resampling.LANCZOS)  # Resize keeping aspect ratio

    # Calculate padding
    padding_left = (256 - img.width) // 2
    padding_top = (192 - img.height) // 2

    # Create a new image with the desired size and paste the resized image onto it
    new_img = Image.new("RGBA", (256, 192), (0, 0, 0, 0))  # Transparent background
    new_img.paste(img, (padding_left, padding_top))

    return new_img


def main() -> None:
    collectibles = fetch_collectibles(COLLECTIBLES_URL)
    if collectibles:
        dump_collectibles(collectibles)
        filtered_collectibles = filter_types(collectibles, COLLECTIBLE_TYPES)
        print(len(filtered_collectibles))
        save_image(filtered_collectibles, OUTPUT_FOLDER)


if __name__ == "__main__":
    main()
