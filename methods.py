import requests
from dotenv import load_dotenv

import os
from pprint import pprint

load_dotenv()

TOKEN_OL = os.getenv("TOKEN_OL")

def get_file_by_id(file_id: int):
    file_resp = requests.post(
        f"{TOKEN_OL}disk.file.get.json",
        json={
            "id": file_id
        }
    ).json()

    if "result" in file_resp:
        file_info = file_resp["result"]
        file_name = file_info["NAME"]
        download_url = file_info["DOWNLOAD_URL"]

        print(f"Downloading file: {file_name} from: {download_url}")

        file_response = requests.get(download_url)

        with open(file_name, "wb") as f:
            f.write(file_response.content)

        print("File downloaded and saved successfully")
        pprint(file_resp)
    else:
        print("Failed to retrieve file info")
        pprint(file_resp)


def merge_dialogs(client_id: int):
    """
    This feature will be implemented in future.
    """
    ...

