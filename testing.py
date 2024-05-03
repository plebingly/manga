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

def download_images(manga_name, chapter_number, image_urls, IMAGE_DIR):
    downloaded = False
    downloaded_images = []
    for i in range(1, 1000):
        image_number = str(i).zfill(3)
        for image_url in image_urls:
            try:
                response = requests.get(image_url.format(image_number=image_number))
                if response.status_code == 200:
                    with open(os.path.join(IMAGE_DIR, f"image_{image_number}.png"), "wb") as file:
                        file.write(response.content)
                    downloaded_images.append(image_number)
                    print(f"Downloaded and saved image {image_number}")
                    downloaded = True
                    break
            except Exception as e:
                print(f"Error downloading image {image_number} from {image_url}: {e}")
        else:
            print(f"Unable to download image {image_number}")
        if not downloaded:
            break
        else:
            downloaded = False

    return downloaded_images

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        delete_images = request.form.get('delete_images')
        if delete_images == 'yes':
            delete_files_in_folder('15b_ubaElxDFbdCJyFWDX9qLM5vxJbFwS')
            print("Images in Google Drive folder deleted.")
        elif delete_images == 'no':
            print("Images in Google Drive folder will be kept.")

        IMAGE_DIR = os.path.join(os.getcwd(), "manga-images")
        os.makedirs(IMAGE_DIR, exist_ok=True)

        manga_name = request.form.get('manga_name').title().replace(" ", "-")
        chapter_number = request.form.get('chapter_number').zfill(4)

        if manga_name.lower() == "zoro-x-sanji":
            image_urls = ["https://i3.nhentai.net/galleries/1166299/{page}.jpg"]
            downloaded_images = download_images(manga_name, chapter_number, image_urls, IMAGE_DIR)
        else:
            image_urls = [
                f"https://scans-hot.leanbox.us/manga/{manga_name}/{chapter_number}-{{image_number}}.png",
                f"https://hot.leanbox.us/manga/{manga_name}/{chapter_number}-{{image_number}}.png",
                f"https://scans.lastation.us/manga/{manga_name}/{chapter_number}-{{image_number}}.png"
            ]
            downloaded_images = download_images(manga_name, chapter_number, image_urls, IMAGE_DIR)

        SCOPES = ['https://www.googleapis.com/auth/drive']
        SERVICE_ACCOUNT_FILE = 'manga-webscraping-17ab083d671a.json'
        PARENT_FOLDER_ID = "15b_ubaElxDFbdCJyFWDX9qLM5vxJbFwS"

        def upload_photo(file_path):
            creds = authenticate()
            service = build('drive', 'v3', credentials=creds)
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

        page_number = 1
        for image_number in downloaded_images:
            upload_photo(os.path.join(IMAGE_DIR, f"image_{image_number}.png"))
            page_number += 1

        # Add a delay before deleting the folder
        time.sleep(5)  # 5 seconds delay

        try:
            shutil.rmtree(IMAGE_DIR)
            print(f"Deleted folder: {IMAGE_DIR}")
        except Exception as e:
            print(f"Error deleting folder: {e}")

    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)