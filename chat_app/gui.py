import json, requests, sys, time, tkinter as tk
from tkinter import Canvas, Frame, Scrollbar, Menu, simpledialog, filedialog
from utils import create_tooltip
from rag_search import rag_search
from pdf_understanding import extract_text_from_pdf, infer_context_from_pdf
from inference import get_response
from langchain.memory import ConversationBufferMemory

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

        # Create the drop-down send button
        self.send_menu_button = tk.Menubutton(self.entry_frame, text="Send", bg='#4d4d4d', fg='black', activebackground='#4d4d4d', activeforeground='black')
        self.send_menu = Menu(self.send_menu_button, tearoff=0)
        self.send_menu.add_command(label="Send", command=self.set_send_mode)
        self.send_menu.add_command(label="RAG Search", command=self.show_rag_popup)
        self.send_menu.add_command(label="Extract PDF", command=self.set_pdf_mode)
        self.send_menu_button.config(menu=self.send_menu)
        self.send_menu_button.grid(row=0, column=1, padx=(10, 0))

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

        # Variable to track the current mode (Send or RAG Search, or PDF Search)
        self.current_mode = "Send"
        self.database_name = None

         # Initialize PDF mode related attributes
        self.pdf_mode = False
        self.pdf_upload_button = None
        self.pdf_text = ""

        # Initialize chat history
        self.memory = ConversationBufferMemory()

    def set_send_mode(self):
        self.current_mode = "Send"
        self.send_menu_button.config(text="Send")

    def show_rag_popup(self):
        self.database_name = simpledialog.askstring("RAG Search", "Enter the database name:")
        if self.database_name:
            self.set_rag_mode()

    def set_rag_mode(self):
        self.current_mode = "RAG Search"
        self.send_menu_button.config(text="RAG Search")

    def set_pdf_mode(self):
        """Set the mode to PDF extraction."""
        self.current_mode = "PDF Search"

        self.send_menu_button.config(text="PDF Mode")
        if not self.pdf_upload_button:
            self.pdf_upload_button = tk.Button(self.entry_frame, text="Upload PDF", command=self.upload_pdf, bg='#4d4d4d', fg='black', activebackground='#4d4d4d', activeforeground='black')
            self.pdf_upload_button.grid(row=0, column=3, padx=(10, 0))
        else:
            self.pdf_upload_button.grid()


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
            print("Sending message:", user_message)  # Debug print
            self.last_user_message = user_message
            self.add_message(user_message, "You")
            self.memory.chat_memory.add_user_message(user_message)
            self.entry.delete(0, tk.END)
            self.stop_processing_flag = False  # Reset stop flag

            if self.current_mode == "PDF Search":
                print("PDF Mode Active")  # Debug print
                infer_context_from_pdf(self, self.pdf_text, user_message)
            elif self.current_mode == "Send":
                get_response(self, user_message)
            elif self.current_mode == "RAG Search":
                rag_search(self, user_message)


    def stop_processing(self):
        """Stop processing the response."""
        self.stop_processing_flag = True

    def retry_message(self):
        """Retry sending the last user message."""
        self.stop_processing_flag = False
        if self.current_mode == "Send":
            get_response(self, self.last_user_message)
        elif self.current_mode == "RAG Search":
            rag_search(self, self.last_user_message)

    def upload_pdf(self):
        """Handle PDF upload and extraction."""
        pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if pdf_path:
            self.add_message("PDF extraction in progress...", "System")
            self.root.update_idletasks()
            self.pdf_text = extract_text_from_pdf(pdf_path)
            self.add_message("PDF extraction complete. You can now ask questions about the PDF.", "System")
