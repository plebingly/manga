from flask import Flask, render_template, request
import os
import shutil
import requests
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
import time

app = Flask(__name__)

def authenticate():
    SCOPES = ['https://www.googleapis.com/auth/drive']
    creds = service_account.Credentials.from_service_account_file('manga-webscraping-17ab083d671a.json', scopes=SCOPES)
    return creds

def delete_files_in_folder(folder_id):
    service = build('drive', 'v3', credentials=authenticate())
    page_token = None
    while True:
        response = service.files().list(q=f"'{folder_id}' in parents",
                                        spaces='drive',
                                        fields='nextPageToken, files(id, name)',
                                        pageToken=page_token).execute()
        for file in response.get('files', []):
            try:
                service.files().delete(fileId=file['id']).execute()
                print(f"Deleted file: {file['name']}")
            except Exception as e:
                print(f"Error deleting file {file['name']}: {e}")
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break

def download_and_upload_zoro_sanji():
    # Define the directory for saving images relative to the Flask app root directory
    IMAGE_DIR = os.path.join(os.getcwd(), "manga-images")

    # Ensure the image directory exists
    os.makedirs(IMAGE_DIR, exist_ok=True)

    image_url = "https://i3.nhentai.net/galleries/1166299/{}.jpg"
    page_number = 1
    downloaded_images = []

    while True:
        try:
            response = requests.get(image_url.format(page_number))
            if response.status_code == 200:
                with open(os.path.join(IMAGE_DIR, f"image_{page_number}.jpg"), "wb") as file:
                    file.write(response.content)
                downloaded_images.append(page_number)
                print(f"Downloaded and saved image {page_number}")
                page_number += 1
            else:
                break  # If the response status code is not 200, stop downloading
        except Exception as e:
            print(f"Error downloading image {page_number}: {e}")
            break  # If there's an error, stop downloading

    # Upload downloaded images to Google Drive
    SCOPES = ['https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = 'manga-webscraping-17ab083d671a.json'
    PARENT_FOLDER_ID = "15b_ubaElxDFbdCJyFWDX9qLM5vxJbFwS"

    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)

    for image_number in downloaded_images:
        file_path = os.path.join(IMAGE_DIR, f"image_{image_number}.jpg")
        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [PARENT_FOLDER_ID]
        }
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        print(f'File ID: {file.get("id")}')

    # Delete the temporary image directory
    try:
        shutil.rmtree(IMAGE_DIR)
        print(f"Deleted folder: {IMAGE_DIR}")
    except Exception as e:
        print(f"Error deleting folder: {e}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        delete_images = request.form.get('delete_images')
        if delete_images == 'yes':
            delete_files_in_folder('15b_ubaElxDFbdCJyFWDX9qLM5vxJbFwS')
            print("Images in Google Drive folder deleted.")
        elif delete_images == 'no':
            print("Images in Google Drive folder will be kept.")

        manga_name = request.form.get('manga_name').title().replace(" ", "-")
        if manga_name.lower() == "zoro-x-sanji":
            download_and_upload_zoro_sanji()

    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)