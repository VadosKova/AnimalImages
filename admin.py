from tkinter import *
from tkinter import messagebox, ttk
import socket
import jsonpickle
import requests
import os
from PIL import Image, ImageTk

IP = '127.0.0.1'
PORT = 4000


def send_request(data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((IP, PORT))
        s.send(jsonpickle.encode(data).encode('utf-8'))
        response = s.recv(8192).decode('utf-8')
        return jsonpickle.decode(response)


class AdminPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("Animal Images Admin Panel")
        self.username = None
        self.current_image_url = None
        self.image_references = []
        self.login_screen()