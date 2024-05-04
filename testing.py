from flask import Flask, render_template, request, send_from_directory
import os
import shutil
import requests
import time
import hashlib  # For generating unique directory names

app = Flask(__name__)

def get_user_directory(user_identifier):
    if not user_identifier:
        user_identifier = "default_user"
    user_dir = hashlib.md5(user_identifier.encode()).hexdigest()
    return os.path.join(os.getcwd(), "user_data", user_dir)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_identifier = request.form.get('username')
        user_dir = get_user_directory(user_identifier)
        os.makedirs(user_dir, exist_ok=True)

        IMAGE_DIR = os.path.join(user_dir, "manga-images")
        os.makedirs(IMAGE_DIR, exist_ok=True)

        manga_name = request.form.get('manga_name').title().replace(" ", "-")
        chapter_number = request.form.get('chapter_number').zfill(4)

        image_urls = [
            f"https://scans-hot.leanbox.us/manga/{manga_name}/{chapter_number}-{{image_number}}.png",
            f"https://hot.leanbox.us/manga/{manga_name}/{chapter_number}-{{image_number}}.png",
            f"https://scans.lastation.us/manga/{manga_name}/{chapter_number}-{{image_number}}.png"
        ]

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

        page_number = 1
        for image_number in downloaded_images:
            page_number += 1

        time.sleep(5)

        try:
            shutil.rmtree(IMAGE_DIR)
            print(f"Deleted folder: {IMAGE_DIR}")
        except Exception as e:
            print(f"Error deleting folder: {e}")

    return render_template('index.html')

@app.route('/user-images/<path:filename>')
def get_user_images(filename):
    user_identifier = request.args.get('username')
    user_dir = get_user_directory(user_identifier)
    return send_from_directory(user_dir, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
