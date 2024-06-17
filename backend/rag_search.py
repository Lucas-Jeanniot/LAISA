import requests, json, time, logging
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# Setup logging
logging.basicConfig(level=logging.DEBUG, filename='response_log.log', filemode='a', format='%(asctime)s - %(message)s')

memory = ConversationBufferMemory()

def retrieve_document(database_name, user_message):
    """Retrieve document from OpenSearch."""
    url = f"http://localhost:9200/{database_name}/_search"
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
            return hits[0]["_source"].get("text", "No text found.")
        else:
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error: Unable to contact the database. {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return None

def rag_inference(user_message, document_text):
    """Stream response from the model using LangChain after receiving document context."""
    llm = Ollama(
        model="llama3",
        callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
        verbose=True,
    )
    memory.chat_memory.add_user_message(user_message)
    memory.chat_memory.add_user_message(document_text)

    template = """
    You are LAISA (Local AI Search Application), a desktop chatbot assistant.

    Answer the following question considering the provided document context:

    Document Context: {document_context}

    User question: {user_question}
    """

    try:
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | llm

        response_stream = chain.stream({
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
