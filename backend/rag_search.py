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

def rag_response(user_message, document_text):
    """Stream response from the model using LangChain."""
    llm = Ollama(
        model="llama3",
        callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
        verbose=True,
    )
    memory.chat_memory.add_user_message(user_message)

    try:
        template = """
        You are LAISA (Local AI Search Application), a desktop chatbot assistant.

        Answer the following questions considering the history of the conversation and the provided document context:

        Chat history: {chat_history}
        Document Context: {document_context}

        User question: {user_question}
        """

        chat_history = memory.load_memory_variables({})
        formatted_history = chat_history['history']
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | llm

        response_stream = chain.stream({
            "chat_history": formatted_history,
            "document_context": document_text,
            "user_question": user_message,
        })

        partial_response = ""
        time.sleep(2)

        for response_chunk in response_stream:
            partial_response += response_chunk
            logging.debug(f"Chunk received: {response_chunk.strip()}")
            yield f"data: {response_chunk}@@END_CHUNK\n\n"
            time.sleep(0.1)

        memory.chat_memory.add_ai_message(partial_response)

    except Exception as e:
        yield f"data: {{'error': '{str(e)}'}}\n\n"
        logging.error(f"Error: {str(e)}")
