import tkinter as tk
from tkinter import filedialog
import pygame
import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from PIL import Image, ImageTk
import io

window = tk.Tk()
window.title("Music Player")
pygame.init()
pygame.mixer.init()

# Глобальные переменные
playlist_dir = ""
current_image = None

def play_music():
    global current_image
    file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3")])
    if file_path:
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        show_album_art(file_path)

def stop_music():
    pygame.mixer.music.stop()

def load_playlist():
    global playlist_dir
    playlist_dir = filedialog.askdirectory()
    if not playlist_dir:
        return
        
    playlist_box.delete(0, tk.END)
    files = os.listdir(playlist_dir)
    for file in files:
        if file.endswith(".mp3"):
            playlist_box.insert(tk.END, file)

def play_selected(event):
    global current_image
    selection = playlist_box.curselection()
    if selection:
        index = selection[0]
        filename = playlist_box.get(index)
        full_path = os.path.join(playlist_dir, filename)
        pygame.mixer.music.load(full_path)
        pygame.mixer.music.play()
        show_album_art(full_path)

def show_album_art(file_path):
    global current_image
    image_data = None
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    print(base_name)
    image_path = None
    
    # 1. Пробуем получить обложку из тегов MP3
    try:
        audio = MP3(file_path, ID3=ID3)
        if audio.tags:
            for tag in audio.tags.values():
                if isinstance(tag, APIC):
                    image_data = tag.data
                    break
    except Exception:
        pass  # Пропускаем ошибки чтения тегов
    
    # 2. Если обложка не найдена в тегах, ищем файл изображения в папке
    files = os.listdir(playlist_dir)
    if not image_data:
        # Проверяем все возможные форматы изображений
        for file in files:
            for x in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                if file.endswith(x):
                    possible_path = os.path.join(playlist_dir, file)
                    if os.path.exists(possible_path):
                        image_path = possible_path
                        break
    
    # 3. Если нашли файл изображения, загружаем его
    if image_path:
        try:
            with open(image_path, 'rb') as img_file:
                image_data = img_file.read()
        except Exception:
            pass
    
    # Создаем изображение
    if image_data:
        try:
            image = Image.open(io.BytesIO(image_data))
            image = image.resize((200, 200), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
        except Exception:
            # Если произошла ошибка обработки изображения
            photo = create_default_thumbnail()
    else:
        # Используем заглушку, если изображение не найдено
        photo = create_default_thumbnail()
    
    # Обновляем лейбл с изображением
    album_art_label.configure(image=photo)
    album_art_label.image = photo
    current_image = photo

def create_default_thumbnail():
    """Создает изображение-заглушку"""
    img = Image.new('RGB', (200, 200), color='gray')
    return ImageTk.PhotoImage(img)

# Создаем интерфейс
play_button = tk.Button(window, text="Play Music", command=play_music)
play_button.pack()

stop_button = tk.Button(window, text="Stop Music", command=stop_music)
stop_button.pack()

# Виджет для обложки альбома
album_art_label = tk.Label(window, width=200, height=200, bg='gray')
album_art_label.pack(pady=10)

playlist_box = tk.Listbox(window, width=50)
playlist_box.pack(fill=tk.BOTH, expand=True, pady=5)
playlist_box.bind("<Double-Button-1>", play_selected)

load_button = tk.Button(window, text="Load Playlist", command=load_playlist)
load_button.pack()

# Инициализация заглушки
default_photo = create_default_thumbnail()
album_art_label.configure(image=default_photo)
album_art_label.image = default_photo

window.mainloop()