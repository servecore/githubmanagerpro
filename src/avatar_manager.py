import os
import requests
import threading
from PIL import Image, ImageTk
import customtkinter as ctk
from io import BytesIO

class AvatarManager:
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        # Default avatar placeholder (a simple colored circle or similar could be generated, but for now we'll handle None)
        self.default_avatar = None 

    def get_avatar_path(self, username: str) -> str:
        return os.path.join(self.cache_dir, f"{username}.png")

    def fetch_avatar(self, username: str, callback=None):
        """
        Fetches avatar in a background thread.
        callback(username, image_path) is called when done.
        """
        def _fetch():
            target_path = self.get_avatar_path(username)
            if os.path.exists(target_path):
                # Already cached
                if callback: callback(username, target_path)
                return

            try:
                url = f"https://github.com/{username}.png?size=200"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    with open(target_path, 'wb') as f:
                        f.write(response.content)
                    if callback: callback(username, target_path)
            except Exception as e:
                print(f"Failed to fetch avatar for {username}: {e}")

        threading.Thread(target=_fetch, daemon=True).start()

    def load_avatar_image(self, username: str, size: tuple = (40, 40)):
        """
        Returns a CTkImage if cached, else None.
        """
        path = self.get_avatar_path(username)
        if os.path.exists(path):
            try:
                pil_img = Image.open(path)
                return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
            except:
                return None
        return None
