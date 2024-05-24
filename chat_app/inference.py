import requests,json,time, tkinter as tk

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
