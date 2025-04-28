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