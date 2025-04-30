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

    def clear_widgets(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.image_references = []

    def login_screen(self):
        self.clear_widgets()
        Label(self.root, text="Admin Authorization", font=('Arial', 18)).pack(pady=10)
        Label(self.root, text="Username").pack()
        self.username_entry = Entry(self.root)
        self.username_entry.pack()
        Label(self.root, text="Password").pack()
        self.password_entry = Entry(self.root, show='*')
        self.password_entry.pack()
        Button(self.root, text="Login", command=self.login).pack(pady=10)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        res = send_request({
            "action": "login",
            "username": username,
            "password": password
        })

        if res.get("message") == "Login successful" and res.get("is_admin"):
            self.username = username
            self.main_menu()
        elif res.get("message") == "Login successful":
            messagebox.showerror("Access denied", "You are not an admin")
        else:
            messagebox.showerror("Error", res.get("message", "Unknown error"))

    def main_menu(self):
        self.clear_widgets()
        Label(self.root, text=f"Welcome, Admin {self.username}", font=('Arial', 16)).pack(pady=10)

        Button(self.root, text="Manage Images", command=self.manage_images).pack(pady=5)
        Button(self.root, text="View User Logs", command=self.view_user_logs).pack(pady=5)
        Button(self.root, text="Moderate Reviews", command=self.moderate_reviews).pack(pady=5)
        Button(self.root, text="Manage Users", command=self.manage_users).pack(pady=5)
        Button(self.root, text="Logout", command=self.login_screen).pack(pady=10)

    def manage_images(self):
        self.clear_widgets()
        Label(self.root, text="Manage Images", font=('Arial', 16)).pack(pady=10)

        btn_frame = Frame(self.root)
        btn_frame.pack(pady=10)

        Button(btn_frame, text="Refresh", command=self.show_images).pack(side=LEFT, padx=5)
        Button(btn_frame, text="Back", command=self.main_menu).pack(side=LEFT, padx=5)

        self.tree = ttk.Treeview(self.root, columns=("url", "favorites", "reviews"), show="headings")
        self.tree.heading("url", text="Image URL")
        self.tree.heading("favorites", text="Favorites")
        self.tree.heading("reviews", text="Reviews")
        self.tree.column("url", width=400)
        self.tree.column("favorites", width=100)
        self.tree.column("reviews", width=100)
        self.tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        action_frame = Frame(self.root)
        action_frame.pack(pady=10)

        Button(action_frame, text="View Details", command=self.view_image_details).pack(side=LEFT, padx=5)
        Button(action_frame, text="Delete Image", command=self.delete_selected_image).pack(side=LEFT, padx=5)

        self.show_images()