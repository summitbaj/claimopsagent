
import requests
import os

API_URL = "http://localhost:8000"
FILE_PATH = "test_upload.docx"

def test_api():
    print(f"Checking API at {API_URL}...")
    try:
        # 1. Get sources
        print("1. Getting sources...")
        res = requests.get(f"{API_URL}/knowledge-sources")
        if res.status_code != 200:
            print(f"Failed to get sources: {res.text}")
            return
        print(f"Sources: {res.json()}")

        # 2. Upload file
        print(f"2. Uploading {FILE_PATH}...")
        if not os.path.exists(FILE_PATH):
            # Create a dummy docx if not exists? converting txt to docx is hard without lib.
            # Assuming it exists as seen in file listing.
            print(f"File {FILE_PATH} not found!")
            return

        with open(FILE_PATH, 'rb') as f:
            files = {'file': f}
            res = requests.post(f"{API_URL}/ingest", files=files)
        
        if res.status_code != 200:
            print(f"Failed to upload: {res.text}")
            return
        print(f"Upload result: {res.json()}")

        # 3. Verify upload
        print("3. Verifying upload...")
        res = requests.get(f"{API_URL}/knowledge-sources")
        sources = res.json().get("sources", [])
        found = any(s['filename'] == FILE_PATH for s in sources)
        print(f"File found in sources? {found}")
        print(f"Current sources: {sources}")

        # 4. Delete file
        if found:
            print(f"4. Deleting {FILE_PATH}...")
            res = requests.delete(f"{API_URL}/knowledge-sources/{FILE_PATH}")
            print(f"Delete result: {res.json()}")
            
            # Verify deletion
            res = requests.get(f"{API_URL}/knowledge-sources")
            sources = res.json().get("sources", [])
            found = any(s['filename'] == FILE_PATH for s in sources)
            print(f"File still in sources? {found}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
