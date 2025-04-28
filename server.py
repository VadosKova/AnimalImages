import socket
import jsonpickle
import pyodbc
import requests
import logging


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

    def download_image(self, image_url, save_path):
        try:
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                with open(save_path, 'wb') as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                return {"message": "Downloaded successfully", "image_path": save_path}
            else:
                return {"message": "Failed to download"}
        except Exception as e:
            logging.error(f"Error downloading image: {e}")
            return {"message": "Error"}

    def close_connection(self):
        self.conn.close()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')