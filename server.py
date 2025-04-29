import socket
import jsonpickle
import pyodbc
import requests
import logging
from PIL import Image
import os
import io


class User:
    def __init__(self, username=None, email=None, password=None):
        self.username = username
        self.email = email
        self.password = password

        self.connection_string = ('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=AnimalImages;Trusted_Connection=yes')

    def log_action(self, action):
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO UserLogs (UserID, Action) VALUES ((SELECT UserID FROM Users WHERE Username = ?), ?)', (self.username, action))
                conn.commit()
        except Exception as e:
            logging.error(f"Error logging action: {e}")

    def is_admin(self):
        with pyodbc.connect(self.connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT IsAdmin FROM Users WHERE LOWER(Username) = LOWER(?)', (self.username,))
            result = cursor.fetchone()
            return result and result[0] == 1

    def register_user(self):
        with pyodbc.connect(self.connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO Users (Username, Email, Password) VALUES (?, ?, ?)', (self.username, self.email, self.password))
            conn.commit()
        self.log_action("User registered")

    def check_login(self, input_password):
        with pyodbc.connect(self.connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT Password FROM Users WHERE LOWER(Username) = LOWER(?)', (self.username,))
            result = cursor.fetchone()
            if result and result[0] == input_password:
                self.log_action("User logged in")
                return True
            return False

    def check_username_exists(self):
        with pyodbc.connect(self.connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM Users WHERE LOWER(Username) = LOWER(?)', (self.username,))
            return cursor.fetchone() is not None

    def save_view_history(self, image_url):
        with pyodbc.connect(self.connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO History (UserID, ImageURL) VALUES ((SELECT UserID FROM Users WHERE Username = ?), ?)', (self.username, image_url))
            conn.commit()
        self.log_action("Viewed image")

    def get_images(self, category):
        try:
            if category == "cats":
                response = requests.get('https://cataas.com/cat?json=true')
                if response.status_code == 200:
                    image_url = response.json().get('url')
                else:
                    image_url = None
                    logging.error(f"Failed to fetch cat image, status code: {response.status_code}")
            elif category == "dogs":
                response = requests.get('https://dog.ceo/api/breeds/image/random')
                if response.status_code == 200:
                    image_url = response.json().get('message')
                else:
                    image_url = None
                    logging.error(f"Failed to fetch dog image, status code: {response.status_code}")
            elif category == "birds":
                access_key = "zcM-4apdjE3GtYjE3g2MA3cyORU_Pntf5CD9OFCvNfI"
                response = requests.get(
                    f"https://api.unsplash.com/photos/random?query=bird&client_id={access_key}&count=1")
                if response.status_code == 200:
                    image_url = response.json()[0].get('urls').get('regular')
                else:
                    image_url = None
                    logging.error(f"Failed to fetch bird image, status code: {response.status_code}")
            else:
                image_url = None
                logging.error(f"Invalid category: {category}")

            return image_url
        except Exception as e:
            logging.error(f"Error fetching image: {e}")
            return None

    def add_favorite(self, image_url):
        with pyodbc.connect(self.connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO Favorites (UserID, ImageURL) VALUES ((SELECT UserID FROM Users WHERE Username = ?), ?)', (self.username, image_url))
            conn.commit()
        self.log_action("Added to favorites")

    def add_review(self, image_url, review_text):
        with pyodbc.connect(self.connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO Reviews (UserID, ImageURL, ReviewText) VALUES ((SELECT UserID FROM Users WHERE Username = ?), ?, ?)', (self.username, image_url, review_text))
            conn.commit()
        self.log_action("Added review")

    def get_favorites_with_reviews(self):
        with pyodbc.connect(self.connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT f.ImageURL, r.ReviewText FROM Favorites f LEFT JOIN Reviews r ON f.ImageURL = r.ImageURL WHERE f.UserID = (SELECT UserID FROM Users WHERE Username = ?)', (self.username,))
            result = cursor.fetchall()
            favorites = []
            for row in result:
                favorites.append({
                    "image_url": row[0],
                    "review_text": row[1] if row[1] else "No review"
                })
            return favorites

    def download_image(self, image_url, image_name="downloaded"):
        try:
            response = requests.get(image_url, stream=True)
            if response.status_code != 200:
                logging.error(f"Failed to fetch image from {image_url}, status code: {response.status_code}")
                return {"message": f"Status code: {response.status_code}"}

            if not response.content:
                logging.error(f"Empty response from {image_url}")
                return {"message": "Empty image data"}

            try:
                img = Image.open(io.BytesIO(response.content))
                file_type = img.format.lower() if img.format else 'jpg'
                if file_type not in ['jpg', 'jpeg', 'png']:
                    logging.error(f"Error image format: {file_type}")
                    return {"message": f"Error image format: {file_type}"}
            except Exception as e:
                logging.error(f"Invalid image data from {image_url}: {str(e)}")
                return {"message": f"Invalid image data: {str(e)}"}

            downloads_dir = os.path.abspath(os.path.join(os.getcwd(), "downloads"))
            try:
                os.makedirs(downloads_dir, exist_ok=True)
            except Exception as e:
                logging.error(f"Failed to create directory {downloads_dir}: {str(e)}")
                return {"message": f"Failed to create directory: {str(e)}"}

            file_path = os.path.join(downloads_dir, f"{image_name}.{file_type}")

            try:
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                logging.info(f"Image saved to {file_path}")
            except Exception as e:
                logging.error(f"Failed to save image to {file_path}: {str(e)}")
                return {"message": f"Failed to save image: {str(e)}"}

            self.log_action("Downloaded image")
            return {"message": "Image downloaded", "image_path": file_path}

        except Exception as e:
            logging.error(f"Unexpected error from {image_url}: {str(e)}")
            return {"message": f"Unexpected error: {str(e)}"}

    def get_all_users(self):
        with pyodbc.connect(self.connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT UserID, Username, Email, IsAdmin FROM Users ORDER BY Username')
            return [{"id": row[0], "username": row[1], "email": row[2], "is_admin": row[3]} for row in cursor.fetchall()]



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def client_request(client):
    try:
        req = client.recv(4096).decode('utf-8')
        data = jsonpickle.decode(req)
        action = data.get('action')
        res = {"message": "Unknown action"}

        user = User(username=data.get('username'))

        if action == 'register':
            user = User(username=data['username'], email=data['email'], password=data['password'])
            if user.check_username_exists():
                res = {"message": "Username already registered"}
            else:
                user.register_user()
                res = {"message": "Registration successful"}

        elif action == 'login':
            if user.check_login(data['password']):
                is_admin = user.is_admin()
                res = {"message": "Login successful", "is_admin": is_admin}
            else:
                res = {"message": "Invalid credentials"}

        elif action == 'get_images':
            category = data.get('category')
            image_url = user.get_images(category)
            if image_url:
                res = {"image_url": image_url}
            else:
                res = {"message": "No found"}

        elif action == 'download_image':
            image_url = data['image_url']
            image_name = data.get('image_name', 'downloaded')
            download_result = user.download_image(image_url, image_name)
            res = download_result

        elif action == 'add_favorite':
            image_url = data['image_url']
            user.add_favorite(image_url)
            res = {"message": "Image added to favorites"}

        elif action == 'add_review':
            image_url = data['image_url']
            review_text = data['review_text']
            user.add_review(image_url, review_text)
            res = {"message": "Review added"}

        elif action == 'view_image':
            image_url = data['image_url']
            user.save_view_history(image_url)
            res = {"message": "Image view history saved"}

        elif action == 'get_favorites':
            favorites = user.get_favorites_with_reviews()
            res = {"favorites": favorites}

        client.send(jsonpickle.encode(res).encode('utf-8'))
    except Exception as e:
        logging.error(f"Error: {e}")
        error_res = {"error": "Error processing request"}
        client.send(jsonpickle.encode(error_res).encode('utf-8'))
    finally:
        client.close()


IP = '127.0.0.1'
PORT = 4000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((IP, PORT))
server.listen(2)
print("Сервер запущен...")

while True:
    client, addr = server.accept()
    print(f"Подключение от {addr}")
    client_request(client)