import time
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()

def stream_response(user_message):
    """Stream response from the model using LangChain."""
    llm = Ollama(model="llama3")
    memory.chat_memory.add_user_message(user_message)

    try:
        template = """
        You are Clippy 2.0, a desktop chatbot assistant. 
        
        Answer the following questions considering the history of the conversation:

        Chat history: {chat_history}

        User question: {user_question}
        """

        chat_history = memory.load_memory_variables({})
        formatted_history = chat_history['history']
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | llm

        response_stream = chain.stream({
            "chat_history": formatted_history,
            "user_question": user_message,
        })

        partial_response = ""
        time.sleep(2)

        for response_chunk in response_stream:
            partial_response += response_chunk
            yield f"data: {response_chunk}\n\n"
            time.sleep(0.1)

        memory.chat_memory.add_ai_message(partial_response)

    except Exception as e:
        yield f"data: {{'error': '{str(e)}'}}\n\n"