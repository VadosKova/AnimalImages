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