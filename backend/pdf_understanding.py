import PyPDF2
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
import time

memory = ConversationBufferMemory()

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    pdf_text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                pdf_text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
    return pdf_text

def infer_context_from_pdf(pdf_text, user_message):
    """Infer context from the extracted PDF text using the LLM with streaming."""
    if not pdf_text:
        return {"error": "No text extracted from PDF."}

    llm = Ollama(model="llama3")

    prompt_template = """
    You are a helpful assistant. Answer the following question considering the provided document context:

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
    time.sleep(2)

    for response_chunk in response_stream:
        partial_response += response_chunk

    memory.chat_memory.add_ai_message(partial_response)
    return {"response": partial_response}
