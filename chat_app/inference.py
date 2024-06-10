import json
import time
import tkinter as tk
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate

def get_response(self, user_message):
    """Get a response from the model using LangChain with streaming."""
    llm = Ollama(model="llama3")

    # Add the user's message to the LangChain memory
    self.memory.chat_memory.add_user_message(user_message)
    response_bubble = self.add_message("", "Model")

    try:
        template = """
        You are Clippy 2.0, a desktop chatbot assistant. 
        
        Answer the following questions considering the history of the conversation:

        Chat history: {chat_history}

        User question: {user_question}
        """

        # Format chat history for the prompt
        chat_history = self.memory.load_memory_variables({})
        formatted_history = chat_history['history']
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | llm

        # Initialize streaming
        response_stream = chain.stream({
            "chat_history": formatted_history,
            "user_question": user_message,
        })

        partial_response = ""
        time.sleep(2)  # Add delay before starting to process chunks

        for response_chunk in response_stream:
            if self.stop_processing_flag:
                print("Processing stopped by user.")
                break

            partial_response += response_chunk

            for label in response_bubble.winfo_children():
                if isinstance(label, tk.Label):
                    label.config(text=partial_response)

            self.chat_canvas.update_idletasks()
            if not self.user_scrolled_up:
                self.chat_canvas.yview_moveto(1.0)
            self.root.update_idletasks()
            self.root.update()

        # Add the model's response to the LangChain memory
        self.memory.chat_memory.add_ai_message(partial_response)

    except Exception as e:
        self.add_message(f"Error: {str(e)}", "System")