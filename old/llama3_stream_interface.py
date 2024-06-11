import subprocess, sys, socket, atexit, requests, json, time
import tkinter as tk
from tkinter import Canvas, Frame, Scrollbar, Menu

# Function to install required packages
def install_packages():
    try:
        import requests
    except ImportError:
        print("requests package not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])

# Call the function to install packages
install_packages()

# Function to check if a specific port is listening
def is_port_listening(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# Function to start the Ollama server
def start_ollama_server():
    print("Starting Ollama server...")
    return subprocess.Popen(["Ollama", "serve"])

# Function to stop the Ollama server
def stop_ollama_server(server_process):
    print("Stopping Ollama server...")
    server_process.terminate()
    server_process.wait()

# Check if port 11434 is listening, if not, start the Ollama server
ollama_server_process = None
if not is_port_listening(11434):
    ollama_server_process = start_ollama_server()

# Ensure the Ollama server is stopped when the program exits
if ollama_server_process:
    atexit.register(stop_ollama_server, ollama_server_process)

# Main chat application class
class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Interface")
        self.root.configure(bg='#2e2e2e')
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Main frame for the chat application
        self.main_frame = Frame(root, bg='#2e2e2e')
        self.main_frame.grid(sticky="nsew")
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        # Canvas to hold the chat messages
        self.chat_canvas = Canvas(self.main_frame, bg='#2e2e2e', highlightthickness=0)
        self.chat_canvas.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Scrollbar for the chat messages
        self.scrollbar = Scrollbar(self.main_frame, command=self.chat_canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        self.chat_canvas.config(yscrollcommand=self.scrollbar.set)

        # Frame to hold the chat messages inside the canvas
        self.message_frame = Frame(self.chat_canvas, bg='#2e2e2e')
        self.message_frame_id = self.chat_canvas.create_window((0, 0), window=self.message_frame, anchor="nw")

        # Bind events for resizing and scrolling
        self.message_frame.bind("<Configure>", self.on_frame_configure)
        self.chat_canvas.bind("<Configure>", self.on_canvas_configure)
        self.root.bind("<Configure>", self.on_root_resize)

        # Entry frame for user input
        self.entry_frame = Frame(self.main_frame, bg='#2e2e2e')
        self.entry_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew")
        self.entry_frame.columnconfigure(0, weight=1)

        # Text entry box for user input
        self.entry = tk.Entry(self.entry_frame, width=50, bg='#4d4d4d', fg='white', insertbackground='white')
        self.entry.grid(row=0, column=0, sticky="ew")
        self.entry.bind("<Return>", self.send_message)

        # Send button
        self.send_button = tk.Button(self.entry_frame, text="Send", command=self.send_message, bg='#4d4d4d', fg='black', activebackground='#4d4d4d', activeforeground='black')
        self.send_button.grid(row=0, column=1, padx=(10, 0))

        # Stop button to stop the processing of a response
        self.stop_button = tk.Button(self.entry_frame, text="Stop", command=self.stop_processing, bg='#4d4d4d', fg='black', activebackground='#4d4d4d', activeforeground='black')
        self.stop_button.grid(row=0, column=2, padx=(10, 0))

        # Flag to control stopping the processing
        self.stop_processing_flag = False

        # Variable to store the last user message
        self.last_user_message = ""

        # Flag to track if user has scrolled up
        self.user_scrolled_up = False

        # Bind mouse wheel event to the chat canvas for scrolling
        self.bind_mousewheel()

    def on_frame_configure(self, event=None):
        """Update the scroll region of the canvas when the frame is configured."""
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))

    def on_canvas_configure(self, event=None):
        """Adjust the width of the message frame to match the canvas width."""
        canvas_width = event.width
        self.chat_canvas.itemconfig(self.message_frame_id, width=canvas_width)

    def on_root_resize(self, event=None):
        """Update message wrap length when the root window is resized."""
        self.update_message_wraplength()

    def on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling."""
        scroll = -1 if event.delta > 0 or event.num == 4 else 1
        self.chat_canvas.yview_scroll(scroll, "units")
        self.user_scrolled_up = scroll == -1

    def bind_mousewheel(self):
        """Enable scrolling with the mouse wheel when the cursor is over the canvas."""
        if sys.platform == "darwin":
            self.chat_canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)  # macOS
        else:
            self.chat_canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)  # Windows and Linux
            self.chat_canvas.bind_all("<Button-4>", self.on_mouse_wheel)  # Linux
            self.chat_canvas.bind_all("<Button-5>", self.on_mouse_wheel)  # Linux

    def update_message_wraplength(self):
        """Update the wrap length of messages based on canvas width."""
        wraplength = self.chat_canvas.winfo_width() - 40
        for widget in self.message_frame.winfo_children():
            for label in widget.winfo_children():
                if isinstance(label, tk.Label):
                    label.config(wraplength=wraplength)

    def add_message(self, message, sender):
        """Add a message to the chat interface."""
        bubble_color, text_color, anchor = ('#4d4d4d', 'white', 'e') if sender == "You" else ('#3a3a3a', 'white', 'w')

        # Create a frame for the message bubble
        bubble = tk.Frame(self.message_frame, bg=bubble_color, bd=5)
        bubble.pack(anchor=anchor, padx=10, pady=5, ipadx=5, ipady=5, fill='x', expand=True)

        # Split message by code blocks
        parts = message.split('```')
        wraplength = self.chat_canvas.winfo_width() - 40
        for i, part in enumerate(parts):
            font = ('Courier', 12) if i % 2 else ('Arial', 12)
            msg_label = tk.Label(bubble, text=part, bg=bubble_color, fg=text_color, font=font, wraplength=wraplength, justify=tk.LEFT, anchor='w')
            msg_label.pack(fill='x', expand=True, anchor='w')

        if sender == "Model":
            # Create a frame to hold the buttons and ensure alignment
            button_frame = tk.Frame(self.message_frame, bg='#2e2e2e')
            button_frame.pack(anchor='w', padx=10, pady=(0, 5))

            # Create a retry button for the model responses
            retry_button = tk.Label(button_frame, text="⟳", bg='#2e2e2e', fg='white', font=("Arial", 16, "bold"))
            retry_button.pack(side='left', padx=(0, 5))
            retry_button.bind("<Button-1>", lambda e: self.retry_message())

            # Create a copy button for the model responses
            copy_button = tk.Label(button_frame, text="📋", bg='#2e2e2e', fg='white', font=("Arial", 12, "bold"))
            copy_button.pack(side='left')
            copy_button.bind("<Button-1>", lambda e, b=bubble: self.copy_to_clipboard(b))

            # Function to create a tooltip
            def create_tooltip(widget, text):
                tooltip = tk.Toplevel(widget)
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry("+0+0")
                label = tk.Label(tooltip, text=text, bg='#2e2e2e', fg='white', font=("Arial", 10), bd=1, relief="solid")
                label.pack()

                def enter(event):
                    x = event.x_root + 10
                    y = event.y_root + 10
                    tooltip.wm_geometry(f"+{x}+{y}")
                    tooltip.deiconify()

                def leave(event):
                    tooltip.withdraw()

                widget.bind("<Enter>", enter)
                widget.bind("<Leave>", leave)
                tooltip.withdraw()

            # Create tooltips for the buttons
            create_tooltip(retry_button, "Retry")
            create_tooltip(copy_button, "Copy")

        self.chat_canvas.update_idletasks()
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        if not self.user_scrolled_up:
            self.chat_canvas.yview_moveto(1.0)
        return bubble

    def copy_to_clipboard(self, bubble):
        """Copy text to clipboard."""
        text = ""
        for label in bubble.winfo_children():
            if isinstance(label, tk.Label):
                text += label.cget("text") + "\n"
        self.root.clipboard_clear()
        self.root.clipboard_append(text.strip())
        self.root.update()  # now it stays on the clipboard after the window is closed



    def send_message(self, event=None):
        """Handle sending of a message."""
        user_message = self.entry.get()
        if user_message:
            self.last_user_message = user_message
            self.add_message(user_message, "You")
            self.entry.delete(0, tk.END)
            self.stop_processing_flag = False  # Reset stop flag
            self.get_response(user_message)

    def stop_processing(self):
        """Stop processing the response."""
        self.stop_processing_flag = True

    def retry_message(self):
        """Retry sending the last user message."""
        self.stop_processing_flag = False
        self.get_response(self.last_user_message)

    def get_response(self, user_message):
        """Get a response from the model."""
        payload = {
            "model": "llama3",
            "messages": [{"role": "user", "content": user_message}],
            "stream": True
        }
        headers = {'Content-Type': 'application/json'}

        # Add an empty message bubble for the response
        response_bubble = self.add_message("", "Model")

        try:
            # Make a POST request to the model server with streaming enabled
            with requests.post("http://localhost:11434/api/chat", data=json.dumps(payload), headers=headers, stream=True) as response:
                response.raise_for_status()
                partial_response = ""
                time.sleep(2)  # Add delay before starting to process chunks
                for line in response.iter_lines():
                    if self.stop_processing_flag:
                        print("Processing stopped by user.")
                        break
                    if line:
                        decoded_line = line.decode('utf-8')
                        try:
                            json_response = json.loads(decoded_line)
                            response_chunk = json_response.get('message', {}).get('content', '')
                            partial_response += response_chunk
                            for label in response_bubble.winfo_children():
                                if isinstance(label, tk.Label):
                                    label.config(text=partial_response)
                            self.chat_canvas.update_idletasks()
                            if not self.user_scrolled_up:
                                self.chat_canvas.yview_moveto(1.0)
                            self.root.update_idletasks()
                            self.root.update()
                        except json.JSONDecodeError as e:
                            print(f"Error decoding JSON: {e}")
                        except Exception as e:
                            print(f"Error updating UI: {e}")
        except requests.exceptions.RequestException as e:
            self.add_message(f"Error: Unable to contact the model server. {str(e)}", "System")
        except Exception as e:
            self.add_message(f"Error: {str(e)}", "System")

# Main entry point of the program
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
