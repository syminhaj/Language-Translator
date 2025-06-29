import tkinter as tk
from tkinter import ttk, messagebox
from googletrans import Translator
from gtts import gTTS
import os
import sqlite3
import pyperclip
import uuid
import pygame

pygame.mixer.init()
AUDIO_DIR = 'audio_files'
os.makedirs(AUDIO_DIR, exist_ok=True)

CUSTOM_LANGUAGES = {
    'en': 'english', 'fr': 'french', 'es': 'spanish', 'de': 'german', 'it': 'italian',
    'ja': 'japanese', 'ko': 'korean', 'zh-cn': 'chinese (simplified)', 'kn': 'kannada',
    'ta': 'tamil', 'te': 'telugu', 'mr': 'marathi', 'ur': 'urdu', 'gu': 'gujarati',
    'ra': 'rajasthani', 'be': 'bengali'
}

root = tk.Tk()
root.title('Real-time Language Translator')
root.geometry('800x600')
root.configure(bg='sky blue')

container = tk.Frame(root, bg='sky blue')
container.pack(fill=tk.BOTH, expand=True)

canvas = tk.Canvas(container, bg='sky blue', highlightthickness=0)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scroll_y = tk.Scrollbar(container, orient='vertical', command=canvas.yview)
scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

scroll_frame = tk.Frame(canvas, bg='sky blue')
scroll_frame_id = canvas.create_window((0, 0), window=scroll_frame, anchor='center')

canvas.configure(yscrollcommand=scroll_y.set)
scroll_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.bind('<Configure>', lambda e: canvas.itemconfig(scroll_frame_id, width=e.width))
canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

def get_lang_code(lang_name):
    return next((code for code, name in CUSTOM_LANGUAGES.items() if name == lang_name), None)

def create_database():
    with sqlite3.connect('translation_history.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS translations (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            source_text TEXT, source_lang TEXT,
                            target_text TEXT, target_lang TEXT,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

def insert_translation(source, src_lang, target, tgt_lang):
    with sqlite3.connect('translation_history.db') as conn:
        conn.execute('''INSERT INTO translations (source_text, source_lang, target_text, target_lang)
                        VALUES (?, ?, ?, ?)''', (source, src_lang, target, tgt_lang))

def get_translation_history():
    with sqlite3.connect('translation_history.db') as conn:
        return conn.execute('''SELECT * FROM translations ORDER BY timestamp DESC LIMIT 5''').fetchall()

def create_label(text, font, row):
    tk.Label(scroll_frame, text=text, font=font, bg='sky blue').grid(row=row, column=0, columnspan=2, pady=(10, 0), sticky='ew')

def create_text_widget(height, row):
    txt = tk.Text(scroll_frame, font='arial 10', height=height, wrap=tk.WORD, padx=5, pady=5)
    txt.grid(row=row, column=0, columnspan=2, padx=30, pady=(10, 0), sticky='ew')
    return txt

def create_button(text, command, row, col):
    btn = tk.Button(scroll_frame, text=text, font='arial 12 bold', pady=5, command=command,
                    bg='pink', activebackground='green', fg='black')
    btn.grid(row=row, column=col, pady=(10, 0), sticky='ew', padx=20)
    return btn

tk.Label(scroll_frame, text="", bg='sky blue', height=5).grid(row=0, column=0, columnspan=2)

create_label("LANGUAGE TRANSLATOR", "ARIAL 20 bold", row=1)
create_label("ENTER TEXT", "arial 13 bold", row=2)
Input_text = create_text_widget(5, row=3)
create_label("CONVERTED LANGUAGE TEXT", "arial 13 bold", row=4)
Output_text = create_text_widget(5, row=5)
create_label("TRANSLATION HISTORY", "arial 13 bold", row=6)
History_text = create_text_widget(10, row=7)

langs = list(CUSTOM_LANGUAGES.values())
src_lang = ttk.Combobox(scroll_frame, values=langs, width=22)
src_lang.grid(row=8, column=0, padx=30, pady=(10, 0), sticky='ew')
src_lang.set('CHOOSE SOURCE LANGUAGE')

dest_lang = ttk.Combobox(scroll_frame, values=langs, width=22)
dest_lang.grid(row=8, column=1, padx=30, pady=(10, 0), sticky='ew')
dest_lang.set('CHOOSE TARGET LANGUAGE')

def Translate():
    try:
        text = Input_text.get(1.0, tk.END).strip()
        if not text:
            raise ValueError("Input text is empty")
        src_code = get_lang_code(src_lang.get())
        dest_code = get_lang_code(dest_lang.get())
        if not src_code or not dest_code:
            raise ValueError("Selected language is not supported")
        translated = Translator().translate(text, src=src_code, dest=dest_code)
        Output_text.delete(1.0, tk.END)
        Output_text.insert(tk.END, translated.text)
        insert_translation(text, src_lang.get(), translated.text, dest_lang.get())
    except Exception as e:
        Output_text.delete(1.0, tk.END)
        Output_text.insert(tk.END, f"Error: {e}")

def Speak():
    try:
        text = Output_text.get(1.0, tk.END).strip()
        if not text:
            raise ValueError("No text to speak")
        lang_code = get_lang_code(dest_lang.get())
        tts = gTTS(text=text, lang=lang_code)
        audio_path = f"{AUDIO_DIR}/output_{uuid.uuid4()}.mp3"
        tts.save(audio_path)
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
        insert_translation(text, dest_lang.get(), "Spoken text", "Audio")
    except Exception as e:
        Output_text.delete(1.0, tk.END)
        Output_text.insert(tk.END, f"Speech error: {e}")

def Replay():
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.rewind()
    else:
        pygame.mixer.music.play()

def ShowHistory():
    history = get_translation_history()
    History_text.delete(1.0, tk.END)
    for entry in history:
        History_text.insert(tk.END, f"Source: {entry[1]} ({entry[2]})\nTarget: {entry[3]} ({entry[4]})\n\n")

def DownloadAudio():
    try:
        text = Output_text.get(1.0, tk.END).strip()
        if not text:
            raise ValueError("No text to download")
        lang_code = get_lang_code(dest_lang.get())
        tts = gTTS(text=text, lang=lang_code)
        audio_path = f"{AUDIO_DIR}/output_{uuid.uuid4()}.mp3"
        tts.save(audio_path)
        messagebox.showinfo("Download Complete", "Audio file downloaded successfully!")
    except Exception as e:
        messagebox.showerror("Download Error", f"Download error: {e}")

create_button("Translate", Translate, row=9, col=0)
create_button("Speak", Speak, row=9, col=1)
create_button("Replay", Replay, row=10, col=0)
create_button("Show History", ShowHistory, row=10, col=1)
create_button("Download Audio", DownloadAudio, row=11, col=0)

scroll_frame.grid_rowconfigure(12, weight=1)
tk.Label(scroll_frame, text="", bg='sky blue', height=5).grid(row=12, column=0, columnspan=2)
create_database()
root.mainloop()