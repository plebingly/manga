import asyncio
from flask import Flask, render_template, request
import os
import shutil
import aiohttp
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
            except Exception as e:
                print(f"Error deleting file {file['name']}: {e}")
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break

async def download_image(session, url, path):
    async with session.get(url) as response:
        if response.status == 200:
            image_content = await response.read()
            with open(path, "wb") as file:
                file.write(image_content)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        delete_images = request.form.get('delete_images')
        if delete_images == 'yes':
            delete_files_in_folder('15b_ubaElxDFbdCJyFWDX9qLM5vxJbFwS')
        elif delete_images == 'no':
            pass

        IMAGE_DIR = os.path.join(os.getcwd(), "manga-images")
        os.makedirs(IMAGE_DIR, exist_ok=True)

        manga_name = request.form.get('manga_name').title().replace(" ", "-")
        chapter_number = request.form.get('chapter_number').zfill(4)

        image_urls = [
            f"https://scans-hot.leanbox.us/manga/{manga_name}/{chapter_number}-{{image_number}}.png",
            f"https://hot.leanbox.us/manga/{manga_name}/{chapter_number}-{{image_number}}.png",
            f"https://scans.lastation.us/manga/{manga_name}/{chapter_number}-{{image_number}}.png"
        ]

        async def download_all_images():
            tasks = []
            async with aiohttp.ClientSession() as session:
                for i in range(1, 1000):
                    image_number = str(i).zfill(3)
                    for image_url in image_urls:
                        task = asyncio.create_task(download_image(session, image_url.format(image_number=image_number), os.path.join(IMAGE_DIR, f"image_{image_number}.png")))
                        tasks.append(task)
            await asyncio.gather(*tasks)

        asyncio.run(download_all_images())

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

        async def upload_all_images():
            tasks = []
            for i in range(1, 1000):
                image_number = str(i).zfill(3)
                tasks.append(asyncio.create_task(upload_photo(os.path.join(IMAGE_DIR, f"image_{image_number}.png"))))
            await asyncio.gather(*tasks)

        asyncio.run(upload_all_images())

        time.sleep(5)

        try:
            shutil.rmtree(IMAGE_DIR)
        except Exception as e:
            pass

    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)