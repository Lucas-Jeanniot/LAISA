import subprocess
import sys 
import socket 
import os
import signal 
import atexit

def install_packages():
    try:
        import requests
        import tkinter as tk 
    except ImportError:
        print("Packages not found, Installing...")
        subprocess.check_call([sys.executable,"-m","pip3","install","-r","requirements.txt"])

#Install Packages if needed
install_packages()

import tkinter as tk
from tkinter import Canvas, Frame, Scrollbar
import requests
import json

#Function to check if port 11434 is listening (Model is running)
def is_port_listening(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost',port)) == 0

# Function to start Ollama Server 
def start_ollama_server():
    print("Starting Ollama server...")
    return subprocess.Popen(["Ollama", "serve"])

#Function to stop Ollama server (when user is done)
def stop_ollama_server(server_process):
    print("Stopping Ollama server...")
    server_process.terminate()
    server_process.wait()

# Check if port 11434 is listening, if not, start Ollama Server
ollama_server_process = None 
if not is_port_listening(11434):
    ollama_server_process = start_ollama_server()

# Ensure Ollama Server is stopped when program exits 
if ollama_server_process:
    atexit.register(stop_ollama_server, ollama_server_process)

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Interface")

        # Set dark grey background
        self.root.configure(bg='#2e2e2e')
        
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        
        self.main_frame = tk.Frame(root, bg='#2e2e2e')
        self.main_frame.grid(sticky="nsew")

        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        
        self.chat_canvas = Canvas(self.main_frame, bg='#2e2e2e', highlightthickness=0)
        self.chat_canvas.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.scrollbar = Scrollbar(self.main_frame, command=self.chat_canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        self.chat_canvas.config(yscrollcommand=self.scrollbar.set)
        
        self.message_frame = tk.Frame(self.chat_canvas, bg='#2e2e2e')
        self.chat_canvas.create_window((0, 0), window=self.message_frame, anchor="nw")

        self.message_frame.bind("<Configure>", self.on_frame_configure)
        self.chat_canvas.bind("<Configure>", self.on_canvas_configure)
        self.chat_canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)
        self.root.bind("<Configure>", self.on_root_resize)
        
        self.entry_frame = tk.Frame(self.main_frame, bg='#2e2e2e')
        self.entry_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")

        self.entry_frame.columnconfigure(0, weight=1)
        
        self.entry = tk.Entry(self.entry_frame, width=50, bg='#4d4d4d', fg='white', insertbackground='white')
        self.entry.grid(row=0, column=0, sticky="ew")
        self.entry.bind("<Return>", self.send_message)

        self.send_button = tk.Button(self.entry_frame, text="Send", command=self.send_message, bg='#4d4d4d', fg='black', activebackground='#4d4d4d', activeforeground='black')
        self.send_button.grid(row=0, column=1, padx=(10, 0))

    def on_frame_configure(self, event=None):
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))

    def on_canvas_configure(self, event=None):
        self.chat_canvas.itemconfig(self.message_frame, width=event.width)

    def on_root_resize(self, event=None):
        self.update_message_wraplength()

    def on_mouse_wheel(self, event):
        self.chat_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def update_message_wraplength(self):
        wraplength = self.chat_canvas.winfo_width() - 40
        for widget in self.message_frame.winfo_children():
            for label in widget.winfo_children():
                if isinstance(label, tk.Label):
                    label.config(wraplength=wraplength)

    def add_message(self, message, sender):
        if sender == "You":
            bubble_color = '#4d4d4d'
            text_color = 'white'
            anchor = 'e'
        else:
            bubble_color = '#3a3a3a'
            text_color = 'white'
            anchor = 'w'
        
        bubble = Frame(self.message_frame, bg=bubble_color, bd=5)
        bubble.pack(anchor=anchor, padx=10, pady=5, ipadx=5, ipady=5, fill='x', expand=True)
        
        parts = message.split('```')
        for i, part in enumerate(parts):
            wraplength = self.chat_canvas.winfo_width() - 40
            if i % 2 == 0:
                msg_label = tk.Label(bubble, text=part, bg=bubble_color, fg=text_color, font=('Arial', 12), wraplength=wraplength, justify=tk.LEFT, anchor='w')
            else:
                msg_label = tk.Label(bubble, text=part, bg=bubble_color, fg=text_color, font=('Courier', 12), wraplength=wraplength, justify=tk.LEFT, anchor='w')
            msg_label.pack(fill='x', expand=True, anchor='w')

        self.chat_canvas.update_idletasks()
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        self.chat_canvas.yview_moveto(1.0)

    def send_message(self, event=None):
        user_message = self.entry.get()
        if user_message:
            self.add_message(user_message, "You")
            self.entry.delete(0, tk.END)
            self.get_response(user_message)

    def get_response(self, user_message):
        payload = {
            "model": "llama3",
            "messages": [
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "stream": False
        }
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post("http://localhost:11434/api/chat", data=json.dumps(payload), headers=headers)
            response_json = response.json()
            model_response = response_json['message']['content']
            self.add_message(model_response, "Model")
        except Exception as e:
            self.add_message("Error: Unable to contact the model server.", "System")

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
