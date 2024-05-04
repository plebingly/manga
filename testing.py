from flask import Flask, render_template, request
import os
import shutil
import requests
import time
import hashlib  # For generating unique directory names

app = Flask(__name__)

def get_user_directory(user_identifier):
    # Check if user_identifier is None or empty
    if not user_identifier:
        # Assign a default value or handle it appropriately
        user_identifier = "default_user"

    # Generate a unique directory name for the user using their identifier
    # You can replace hashlib with any other method you prefer for creating unique names
    user_dir = hashlib.md5(user_identifier.encode()).hexdigest()
    return os.path.join(os.getcwd(), "user_data", user_dir)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get user identifier (for example, username)
        user_identifier = request.form.get('username')

        # Get user directory
        user_dir = get_user_directory(user_identifier)

        # Create a directory for the user if it doesn't exist
        os.makedirs(user_dir, exist_ok=True)

        # Define the directory for saving images relative to the user's directory
        IMAGE_DIR = os.path.join(user_dir, "manga-images")
        os.makedirs(IMAGE_DIR, exist_ok=True)

        manga_name = request.form.get('manga_name').title().replace(" ", "-")
        chapter_number = request.form.get('chapter_number').zfill(4)

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

        page_number = 1
        for image_number in downloaded_images:
            # Process the downloaded images as needed
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
