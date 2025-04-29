from tkinter import *
from tkinter import messagebox, filedialog
import socket
import jsonpickle
import requests
import os
from PIL import Image, ImageTk

IP = '127.0.0.1'
PORT = 4000


class AnimalImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Animal Images")
        self.root.geometry("700x700")
        self.root.configure(bg='#f0f0f0')

        self.button_font = ('Arial', 10)
        self.label_font = ('Arial', 10)
        self.header_font = ('Arial', 14, 'bold')

        self.current_user = None
        self.is_admin = False
        self.current_image_url = None
        self.current_category = None
        self.image_references = []

        self.start_screen()

    def clear_widgets(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.image_references = []

    def start_screen(self):
        self.clear_widgets()
        Label(self.root, text="Animal Images", font=self.header_font, bg='#f0f0f0').pack(pady=20)

        Label(self.root, text="Username:").pack()
        self.username_entry = Entry(self.root)
        self.username_entry.pack()

        Label(self.root, text="Password:").pack()
        self.password_entry = Entry(self.root, show="*")
        self.password_entry.pack()

        Button(self.root, text="Login", command=self.login).pack(pady=10)
        Button(self.root, text="Register", command=self.register_screen).pack()