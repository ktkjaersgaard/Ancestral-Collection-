import json
Collection_default = "Collection"
import os
directory = "Collections"
Collection = Collection_default
def Get_Collection():
    if not os.path.exists("config.json"):
            with open("config.json", "w") as file:
                json.dump({}, file, indent=4)

    with open("config.json", "r") as file:
        config = json.load(file)

    name = config.get("File Name", Collection_default)
    full_path = os.path.join(directory, f"{name}.json")

    os.makedirs(directory, exist_ok=True)

    if not os.path.exists(full_path):
        print(f"Warning: {full_path} not found, creating empty collection")
        with open(full_path, "w") as file:
            json.dump({}, file, indent=4)

    return full_path
def Set_Collection(text):
    global Collection
    Collection = text
    with open("config.json","r") as file:
        config = json.load(file)
    config["File Name"] = Collection
    with open("config.json","w") as file:
        json.dump(config, file, indent=4)
    