import PyPDF2
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
import tkinter as tk

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    pdf_text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                pdf_text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
    return pdf_text

def infer_context_from_pdf(self, pdf_text, user_message):
    """Infer context from the extracted PDF text using the LLM with streaming."""
    if not pdf_text:
        self.add_message("Error: No text extracted from PDF.", "System")
        return

    print("Starting PDF inference")  # Debug print

    

    # Initialize LLM
    llm = Ollama(model="llama3")

    # UI element for the response bubble
    response_bubble = self.add_message("", "Model")

    full_response = ""
    
    prompt_template = """
        You are a helpful assistant. Answer the following question considering the provided document context:
        Always answer truthfully, never make up answers, if you do not know the answer, simply say "I don't know that information sorry! Could you provide more context?"
        Answer the following questions considering the history of the conversation, try not to repeat previous instances of the conversation history unless required, if the conversation memory is empty, don't reference that:

        Document Context: {document_context}

        User question: {user_question}
        """
    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = prompt | llm

    formatted_prompt = {
            "document_context": pdf_text,
            "user_question": user_message,
        }

    response_stream = chain.stream(formatted_prompt)

    partial_response = ""
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

    full_response += partial_response

    # Add the model's response to the LangChain memory
    self.memory.chat_memory.add_ai_message(full_response)