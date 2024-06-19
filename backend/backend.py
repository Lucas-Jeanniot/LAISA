from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from inference import stream_response
from rag_search import rag_response
from document_retrieval import retrieve_document
from pdf_understanding import extract_text_from_pdf, infer_context_from_pdf

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        document_text = extract_text_from_pdf(file_path)
        return jsonify({"message": "File uploaded successfully", "document_text": document_text}), 200

@app.route('/api/query', methods=['GET'])
def query():
    user_message = request.args.get('query')
    document_text = request.args.get('document_text')
    if not user_message or not document_text:
        return jsonify({"error": "Please provide both user query and document text"}), 400

    def generate():
        for chunk in infer_context_from_pdf(document_text, user_message):
            yield chunk

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
