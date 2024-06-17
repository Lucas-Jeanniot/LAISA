from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from inference import stream_response
from rag_search import rag_response
from document_retrieval import retrieve_document

app = Flask(__name__)
CORS(app)

@app.route('/api/message', methods=['POST'])
def message():
    data = request.json
    user_message = data['message']
    return jsonify({"message": "Message received", "user_message": user_message}), 200

@app.route('/api/stream', methods=['GET'])
def stream():
    user_message = request.args.get('message')
    return Response(stream_response(user_message), mimetype='text/event-stream')

@app.route('/api/rag_search', methods=['POST'])
def rag_search():
    data = request.json
    database_name = data.get('database_name')
    user_message = data.get('message')
    if not database_name or not user_message:
        return jsonify({"response": "Error: Please provide both database name and user message."}), 400

    document = retrieve_document(database_name, user_message)
    return jsonify(document), 200

@app.route('/api/document_query', methods=['GET'])
def document_query():
    document_text = request.args.get('document_text')
    user_query = request.args.get('query')
    if not document_text or not user_query:
        return jsonify({"response": "Error: Please provide both document text and query."}), 400

    response_generator = rag_response(user_query, document_text)
    return Response(response_generator, mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
