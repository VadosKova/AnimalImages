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

    def register_screen(self):
        self.clear_widgets()
        Label(self.root, text="Register account", font=self.header_font).pack(pady=10)

        fields = [
            ("Username:", "reg_username"),
            ("Email:", "reg_email"),
            ("Password:", "reg_password"),
            ("Confirm password:", "reg_confirm_password")
        ]

        self.register_entries = {}
        for label, name in fields:
            Label(self.root, text=label).pack()
            entry = Entry(self.root)
            if "password" in name:
                entry.config(show="*")
            entry.pack()
            self.register_entries[name] = entry

        Button(self.root, text="Register", command=self.register).pack(pady=10)
        Button(self.root, text="Back", command=self.start_screen).pack()

    def main_menu(self):
        self.clear_widgets()
        Label(self.root, text=f"Welcome, {self.current_user}!", font=self.header_font).pack(pady=20)

        categories_frame = Frame(self.root)
        categories_frame.pack(pady=20)

        Label(categories_frame, text="Choose category:").grid(row=0, column=0, padx=5)
        self.category_var = StringVar()

        categories = [("Cats", "cats"), ("Dogs", "dogs"), ("Birds", "birds")]
        for i, (text, value) in enumerate(categories):
            Radiobutton(categories_frame, text=text, variable=self.category_var,
                        value=value).grid(row=0, column=i + 1, padx=5)

        Button(self.root, text="Show Images", command=self.load_image).pack(pady=10)

        self.image_frame = Frame(self.root, bg='white', width=600, height=400)
        self.image_frame.pack(pady=10, fill=BOTH, expand=True)
        self.image_frame.pack_propagate(False)

        self.image_label = Label(self.image_frame, bg='white')
        self.image_label.pack(fill=BOTH, expand=True)

        actions_frame = Frame(self.root)
        actions_frame.pack(pady=10)

        Button(actions_frame, text="Add to Favorites", command=self.add_to_favorites).grid(row=0, column=0, padx=5)
        Button(actions_frame, text="Add Review", command=self.add_review_dialog).grid(row=0, column=1, padx=5)
        Button(actions_frame, text="Download", command=self.download_image).grid(row=0, column=2, padx=5)

        bottom_frame = Frame(self.root)
        bottom_frame.pack(pady=10)

        Button(bottom_frame, text="View Favorites", command=self.show_favorites).grid(row=0, column=0, padx=5)
        Button(bottom_frame, text="Logout", command=self.logout).grid(row=0, column=1, padx=5)

    def load_image(self):
        category = self.category_var.get()
        if not category:
            messagebox.showwarning("Warning", "Please select a category")
            return

        self.current_category = category

        response = self.send_request({
            "action": "get_images",
            "category": category,
            "username": self.current_user
        })

        if response and "image_url" in response:
            self.current_image_url = response["image_url"]

            self.send_request({
                "action": "view_image",
                "username": self.current_user,
                "image_url": self.current_image_url
            })

            try:
                response = requests.get(self.current_image_url)
                if response.status_code == 200:
                    temp_file = "temp_image.jpg"
                    with open(temp_file, "wb") as f:
                        f.write(response.content)

                    img = Image.open(temp_file)
                    img.thumbnail((self.image_frame.winfo_width(), self.image_frame.winfo_height()))

                    photo = ImageTk.PhotoImage(img)
                    self.image_label.config(image=photo)
                    self.image_label.image = photo
                    self.image_references.append(photo)

                    os.remove(temp_file)
                else:
                    messagebox.showerror("Error", "Failed to load image")
            except Exception as e:
                messagebox.showerror("Error", f"Image loading error: {e}")
        else:
            messagebox.showerror("Error", "Error with server")

    def add_to_favorites(self):
        if not self.current_image_url:
            messagebox.showwarning("Warning", "No image to add")
            return

        response = self.send_request({
            "action": "add_favorite",
            "username": self.current_user,
            "image_url": self.current_image_url
        })

        if response and response.get("message") == "Image added to favorites":
            messagebox.showinfo("Success", "Added to favorites")
        else:
            messagebox.showerror("Error", "Failed to add to favorites")

    def add_review_dialog(self):
        if not self.current_image_url:
            messagebox.showwarning("Warning", "No image to review")
            return

        dialog = Toplevel(self.root)
        dialog.title("Add Review")
        dialog.geometry("400x300")

        Label(dialog, text="Your review:").pack(pady=10)
        review_text = Text(dialog, height=10, width=40)
        review_text.pack(padx=10, pady=5)

        def submit():
            text = review_text.get("1.0", END).strip()
            if not text:
                messagebox.showwarning("Warning", "Cannot be empty")
                return

            response = self.send_request({
                "action": "add_review",
                "username": self.current_user,
                "image_url": self.current_image_url,
                "review_text": text
            })

            if response and response.get("message") == "Review added":
                messagebox.showinfo("Success", "Review added")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to add review")

        Button(dialog, text="Submit", command=submit).pack(pady=10)

    def download_image(self):
        if not self.current_image_url:
            messagebox.showwarning("Warning", "No image to download")
            return

        file_path = filedialog.asksaveasfilename(initialdir=".", title="Save image", defaultextension=".jpg", filetypes=[("JPEG files", "*.jpg"), ("PNG files", "*.png"), ("All files", "*.*")])

        if not file_path:
            return

        image_name = os.path.splitext(os.path.basename(file_path))[0]
        response = self.send_request({
            "action": "download_image",
            "username": self.current_user,
            "image_url": self.current_image_url,
            "image_name": image_name
        })

        if response and response.get("message") == "Image downloaded":
            messagebox.showinfo("Success", f"Image saved on server at {response.get('image_path')}")
        else:
            error_message = response.get("message", "Failed to download image") or "Unknown error"
            messagebox.showerror("Error", f"Download failed: {error_message}")

    def show_favorites(self):
        response = self.send_request({
            "action": "get_favorites",
            "username": self.current_user
        })

        if not response or "favorites" not in response or not response["favorites"]:
            messagebox.showinfo("Info", "You have no favorites yet")
            return

        favorites = response["favorites"]
        fav_window = Toplevel(self.root)
        fav_window.title("My Favorites")
        fav_window.geometry("500x500")

        canvas = Canvas(fav_window)
        scrollbar = Scrollbar(fav_window, orient="vertical", command=canvas.yview)
        scrollable_frame = Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for item in favorites:
            frame = Frame(scrollable_frame)
            frame.pack(fill="x", padx=5, pady=5)

            try:
                temp_file = "temp_fav.jpg"
                with open(temp_file, "wb") as f:
                    f.write(requests.get(item['image_url']).content)

                img = Image.open(temp_file)
                img.thumbnail((300, 300))
                photo = ImageTk.PhotoImage(img)

                label = Label(frame, image=photo)
                label.image = photo
                label.pack()

                if item['review_text'] != "No review":
                    Label(frame, text=f"Review: {item['review_text']}", wraplength=400).pack()

                Button(frame, text="Remove",
                       command=lambda url=item['image_url']: self.remove_favorite(url, fav_window)).pack()

                os.remove(temp_file)
            except Exception as e:
                Label(frame, text=f"Error loading image: {e}").pack()

    def remove_favorite(self, image_url, window):
        response = self.send_request({
            "action": "remove_favorite",
            "username": self.current_user,
            "image_url": image_url
        })

        if response and response.get("message") == "Favorite removed":
            messagebox.showinfo("Success", "Removed from favorites")
            window.destroy()
            self.show_favorites()
        else:
            messagebox.showerror("Error", "Failed to remove")

    def send_request(self, data):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((IP, PORT))
            client.send(jsonpickle.encode(data).encode('utf-8'))
            response = client.recv(4096).decode('utf-8')
            client.close()
            return jsonpickle.decode(response)
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {e}")
            return {"error": str(e)}

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Enter username and password")
            return

        response = self.send_request({
            "action": "login",
            "username": username,
            "password": password
        })

        if response.get("message") == "Login successful":
            self.current_user = username
            self.is_admin = response.get("is_admin", False)
            self.main_menu()
        else:
            messagebox.showerror("Error", response.get("message", "Login failed"))