import requests, json, time
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
import tkinter as tk

memory = ConversationBufferMemory()

def rag_search(self, user_message):
    """Perform a RAG search with the model."""
    if not self.database_name:
        self.add_message("Error: No database name provided.", "System")
        return

    url = f"http://localhost:9200/{self.database_name}/_search"
    payload = {
        "_source": {
            "excludes": ["passage_embedding"]
        },
        "query": {
            "neural": {
                "passage_embedding": {
                    "query_text": user_message,
                    "model_id": "y4L5WI8BlCBJfWriuN92",
                    "k": 1
                }
            }
        }
    }

    try:
        response = requests.get(url, params={"source": json.dumps(payload), "source_content_type": "application/json"})
        response.raise_for_status()
        results = response.json()
        hits = results.get("hits", {}).get("hits", [])
        if hits:
            for hit in hits:
                text = hit["_source"].get("text", "No text found.")
                # Send the retrieved document to the model for context inference
                send_document_to_model(self, user_message, text)
        else:
            self.add_message("No results found.", "System")
    except requests.exceptions.RequestException as e:
        self.add_message(f"Error: Unable to contact the database. {str(e)}", "System")
    except Exception as e:
        self.add_message(f"Error: {str(e)}", "System")

def send_document_to_model(self, user_message, document_text):
    """Send the retrieved document to the model for context inference."""
    # Initialize LLM
    llm = Ollama(model="llama3")

    # Add the user's message and document text to the LangChain memory
    memory.chat_memory.add_user_message(user_message)
    memory.chat_memory.add_user_message(document_text)

    response_bubble = self.add_message("", "Model")

    try:
        prompt_template = """
        You are a helpful assistant. Answer the following question considering the provided document context:

        Document Context: {document_context}

        User question: {user_question}
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | llm

        formatted_prompt = {
            "document_context": document_text,
            "user_question": user_message,
        }

        response_stream = chain.stream(formatted_prompt)

        partial_response = ""
        time.sleep(2)  # Add delay before starting to process chunks

        for response_chunk in response_stream:
            if self.stop_processing_flag:
                print("Processing stopped by user.")
                break

            partial_response += response_chunk
            print(f"Chunk: {response_chunk}")  # Debug print to trace responses

            for label in response_bubble.winfo_children():
                if isinstance(label, tk.Label):
                    label.config(text=partial_response)

            self.chat_canvas.update_idletasks()
            if not self.user_scrolled_up:
                self.chat_canvas.yview_moveto(1.0)
            self.root.update_idletasks()
            self.root.update()

        # Add the model's response to the LangChain memory
        memory.chat_memory.add_ai_message(partial_response)
        print("Full Response:", partial_response)  # Debug print to trace full response

    except Exception as e:
        self.add_message(f"Error: {str(e)}", "System")