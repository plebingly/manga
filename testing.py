import os
import shutil
import requests
from googleapiclient.discovery import build
from google.oauth2 import service_account
import time

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

delete_images = input("Would you like to delete all of the images in the Google Drive folder before you continue? (yes/no): ").lower()

if delete_images == 'yes':
    delete_files_in_folder('15b_ubaElxDFbdCJyFWDX9qLM5vxJbFwS')
    print("Images in Google Drive folder deleted.")
elif delete_images == 'no':
    print("Images in Google Drive folder will be kept.")

# Continue with the rest of the code
path = "manga-images"
os.makedirs(path, exist_ok=True)

manga_name = input("What is the name of the Manga? ")
manga_name = manga_name.title()
manga_name = manga_name.replace(" ", "-")

chapter_number = input("What chapter number would you like? ")
chapter_number_with_format = chapter_number.zfill(4)

image_urls = [
    f"https://scans-hot.leanbox.us/manga/{manga_name}/{chapter_number_with_format}-{{image_number}}.png",
    f"https://hot.leanbox.us/manga/{manga_name}/{chapter_number_with_format}-{{image_number}}.png",
    f"https://scans.lastation.us/manga/{manga_name}/{chapter_number_with_format}-{{image_number}}.png"
]

downloaded = False  # Track if any images were downloaded
downloaded_images = []  # Track the downloaded images

for i in range(1, 1000):
    image_number = str(i).zfill(3)
    for image_url in image_urls:
        try:
            response = requests.get(image_url.format(image_number=image_number))
            if response.status_code == 200:
                with open(f"{path}/image_{image_number}.png", "wb") as file:
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

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'manga-webscraping-17ab083d671a.json'
PARENT_FOLDER_ID = "15b_ubaElxDFbdCJyFWDX9qLM5vxJbFwS"

def upload_photo(file_path):
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    file_metadata = {
        'name' : f"page {page_number}",
        'parents' : [PARENT_FOLDER_ID]
    }

    file = service.files().create(
         body=file_metadata,
        media_body=file_path
    ).execute()
 
page_number = 1
for image_number in downloaded_images:
    upload_photo(f"C:\\Games\\Coding\\manga-images\\image_{image_number}.png")
    page_number += 1

# Add a delay before deleting the folder
time.sleep(5)  # 5 seconds delay

absolute_path = os.path.abspath(path)

try:
    shutil.rmtree(absolute_path)
    print(f"Deleted folder: {absolute_path}")
except Exception as e:
    print(f"Error deleting folder: {e}")