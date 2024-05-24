import subprocess
import socket

def start_ollama_server():
    print("Starting Ollama server...")
    return subprocess.Popen(["Ollama", "serve"])

def stop_ollama_server(server_process):
    print("Stopping Ollama server...")
    server_process.terminate()
    server_process.wait()

def is_port_listening(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0
