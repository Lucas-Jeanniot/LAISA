import PyPDF2
import time
import logging
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# Setup logging
logging.basicConfig(level=logging.DEBUG, filename='response_log.log', filemode='a', format='%(asctime)s - %(message)s')

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

    llm = Ollama(
        model="llama3",
        callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
        verbose=True,
    )

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
        logging.debug(f"Chunk received: {response_chunk.strip()}")
        yield f"data: {response_chunk}@@END_CHUNK\n\n"
        time.sleep(0.1)

    memory.chat_memory.add_ai_message(partial_response)
