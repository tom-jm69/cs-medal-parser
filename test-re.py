import os
import json
from config import DUMP_FOLDER, COLLECTIBLE_TYPES
from main import filter_types



newest_file = None
newest_creation_time = 0  # Initialize with a time value that is definitely smaller than any file's creation time

for file in os.listdir(DUMP_FOLDER):
    file_path = os.path.join(DUMP_FOLDER, file)
    
    if file.endswith(".json"):
        # Get the file's creation time
        creation_time = os.path.getctime(file_path)
        
        # If this file is newer than the previous ones, update the newest file
        if creation_time > newest_creation_time:
            newest_file = file
            newest_creation_time = creation_time

if newest_file:
    print(f"The newest file is: {newest_file}")
    with open(f"{DUMP_FOLDER}{newest_file}", "r") as f:
        data = json.load(f)
        filtered = filter_types(data, COLLECTIBLE_TYPES)
        print(filtered)
        with open("filtered.json", "w") as f:
            f.write(json.dumps(filtered))
else:
    print("No JSON files found.")
