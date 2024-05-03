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

def download_zoro_x_sanji_images():
    # Define the directory for saving images relative to the Flask app root directory
    IMAGE_DIR = os.path.join(os.getcwd(), "manga-images")

    # Ensure the image directory exists
    os.makedirs(IMAGE_DIR, exist_ok=True)

    # Define the base URL for zoro x sanji
    base_url = "https://i3.nhentai.net/galleries/1166299/"

    # Initialize the page number
    page_number = 1

    # Loop to download images
    while True:
        try:
            # Construct the image URL
            image_url = f"{base_url}{page_number}.jpg"
            # Download the image
            response = requests.get(image_url)
            if response.status_code == 200:
                # Save the image
                with open(os.path.join(IMAGE_DIR, f"image_{page_number}.jpg"), "wb") as file:
                    file.write(response.content)
                print(f"Downloaded and saved image {page_number}")
                # Increment page number
                page_number += 1
            else:
                # If the response status code is not 200, stop downloading
                break
        except Exception as e:
            print(f"Error downloading image {page_number}: {e}")

    # Continue with the rest of the code (uploading images to Google Drive, etc.)
    upload_images_to_drive(IMAGE_DIR)

def upload_images_to_drive(image_dir):
    SCOPES = ['https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = 'manga-webscraping-17ab083d671a.json'
    PARENT_FOLDER_ID = "15b_ubaElxDFbdCJyFWDX9qLM5vxJbFwS"

    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)

    # Iterate over image files in the directory
    for filename in os.listdir(image_dir):
        if filename.endswith(".jpg"):
            file_path = os.path.join(image_dir, filename)
            # Upload each image file to Google Drive
            file_metadata = {
                'name': filename,
                'parents': [PARENT_FOLDER_ID]
            }
            media = MediaFileUpload(file_path, resumable=True)
            try:
                file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                print(f'File ID: {file.get("id")}')
            except Exception as e:
                print(f"Error uploading file {filename}: {e}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        delete_images = request.form.get('delete_images')
        if delete_images == 'yes':
            delete_files_in_folder('15b_ubaElxDFbdCJyFWDX9qLM5vxJbFwS')
            print("Images in Google Drive folder deleted.")
        elif delete_images == 'no':
            print("Images in Google Drive folder will be kept.")

        # Define the directory for saving images relative to the Flask app root directory
        IMAGE_DIR = os.path.join(os.getcwd(), "manga-images")

        # Ensure the image directory exists
        os.makedirs(IMAGE_DIR, exist_ok=True)

        manga_name = request.form.get('manga_name').title().replace(" ", "-")
        chapter_number = request.form.get('chapter_number').zfill(4)

        if manga_name.lower() == "zoro-x-sanji":
            download_zoro_x_sanji_images()
        else:
            # Original image downloading process
            image_urls = [
                f"https://scans-hot.leanbox.us/manga/{manga_name}/{chapter_number}-{{image_number}}.png",
                f"https://hot.leanbox.us/manga/{manga_name}/{chapter_number}-{{image_number}}.png",
                f"https://scans.lastation.us/manga/{manga_name}/{chapter_number}-{{image_number}}.png"
            ]

            downloaded = False  # Track if any images were downloaded
            downloaded_images = []  # Track the downloaded images

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
                            downloaded = True  # Set downloaded to True if any image was downloaded
                            break  # Break the inner loop if successful
                    except Exception as e:
                        print(f"Error downloading image {image_number} from {image_url}: {e}")
                else:
                    # If none of the image URLs worked, print an error message
                    print(f"Unable to download image {image_number}")

                if not downloaded:
                    # If no images were downloaded in this iteration, break the loop
                    break
                else:
                    downloaded = False  # Reset downloaded for the next iteration

            upload_images_to_drive(IMAGE_DIR)

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