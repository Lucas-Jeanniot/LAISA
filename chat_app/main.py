import tkinter as tk
from gui import ChatApp
from server import start_ollama_server, stop_ollama_server, is_port_listening
import atexit

if __name__ == "__main__":
    # Check if port 11434 is listening, if not, start the Ollama server
    ollama_server_process = None
    if not is_port_listening(11434):
        ollama_server_process = start_ollama_server()

    # Ensure the Ollama server is stopped when the program exits
    if ollama_server_process:
        atexit.register(stop_ollama_server, ollama_server_process)

    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
