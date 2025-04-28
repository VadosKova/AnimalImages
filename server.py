import socket
import jsonpickle
import pyodbc
import requests
import logging
from PIL import Image
import os


class User:
    def __init__(self, username=None, email=None, password=None):
        self.username = username
        self.email = email
        self.password = password

        self.connection_string = ('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=AnimalImages;Trusted_Connection=yes')
        self.conn = pyodbc.connect(self.connection_string)
        self.cursor = self.conn.cursor()


    def is_admin(self):
        self.cursor.execute('SELECT IsAdmin FROM Users WHERE LOWER(Username) = LOWER(?)', (self.username,))
        result = self.cursor.fetchone()
        return result and result[0] == 1

    def register_user(self):
        self.cursor.execute('INSERT INTO Users (Username, Email, Password) VALUES (?, ?, ?)', (self.username, self.email, self.password))
        self.conn.commit()

    def check_login(self, input_password):
        self.cursor.execute('SELECT Password FROM Users WHERE LOWER(Username) = LOWER(?)', (self.username,))
        result = self.cursor.fetchone()
        if result:
            return result[0] == input_password
        return False

    def check_username_exists(self):
        self.cursor.execute('SELECT * FROM Users WHERE LOWER(Username) = LOWER(?)', (self.username,))
        return self.cursor.fetchone() is not None

    def save_view_history(self, image_url):
        self.cursor.execute('INSERT INTO History (UserID, ImageURL) VALUES ((SELECT UserID FROM Users WHERE Username = ?), ?)', (self.username, image_url))
        self.conn.commit()

    def get_images(self, category):
        if category == "cats":
            response = requests.get('https://cataas.com/cat?json=true')
            image_url = response.json().get('url')
        elif category == "dogs":
            response = requests.get('https://dog.ceo/dog-api/')
            image_url = response.json().get('message')
        elif category == "birds":
            access_key = "zcM-4apdjE3GtYjE3g2MA3cyORU_Pntf5CD9OFCvNfI"
            response = requests.get(f'https://api.unsplash.com/photos/random?query=bird&client_id={access_key}')
            image_url = response.json()[0].get('urls').get('regular')
        else:
            image_url = None
        return image_url

    def add_favorite(self, image_url):
        self.cursor.execute('INSERT INTO Favorites (UserID, ImageURL) VALUES ((SELECT UserID FROM Users WHERE Username = ?), ?)', (self.username, image_url))
        self.conn.commit()

    def add_review(self, image_url, review_text):
        self.cursor.execute('INSERT INTO Reviews (UserID, ImageURL, ReviewText) VALUES ((SELECT UserID FROM Users WHERE Username = ?), ?, ?)', (self.username, image_url, review_text))
        self.conn.commit()

    def get_favorites_with_reviews(self):
        self.cursor.execute('SELECT f.ImageURL, r.ReviewText FROM Favorites f LEFT JOIN Reviews r ON f.ImageURL = r.ImageURL WHERE f.UserID = (SELECT UserID FROM Users WHERE Username = ?)', (self.username,))
        result = self.cursor.fetchall()
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
            if response.status_code == 200:
                img = Image.open(response.raw)
                file_type = img.format.lower()

                os.makedirs("downloads", exist_ok=True)
                file_path = os.path.join("downloads", f"{image_name}.{file_type}")

                image_bytes = requests.get(image_url).content
                with open(file_path, 'wb') as f:
                    f.write(image_bytes)

                return {"message": "Image downloaded", "image_path": file_path}
            else:
                return {"message": "Failed to download", "status_code": response.status_code}
        except Exception as e:
            logging.error(f"Error downloading image: {e}")
            return {"message": "Error"}

    def close_connection(self):
        self.conn.close()

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

    except Exception as e:
        logging.error(f"Error: {e}")
        error_res = {"error": "Error processing request"}
        client.send(jsonpickle.encode(error_res).encode('utf-8'))
    finally:
        client.close()