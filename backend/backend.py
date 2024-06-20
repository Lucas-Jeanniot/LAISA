from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from inference import stream_response
from rag_search import rag_response
from document_retrieval import retrieve_document
from pdf_understanding import extract_text_from_pdf, infer_context_from_pdf

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/message', methods=['POST'])
def message():
    data = request.json
    user_message = data['message']
    model = data.get('model', 'llama3')  # Default to 'llama3' if model is not provided
    return jsonify({"message": "Message received", "user_message": user_message, "model": model}), 200

@app.route('/api/stream', methods=['GET'])
def stream():
    user_message = request.args.get('message')
    model = request.args.get('model', 'llama3')  # Default to 'llama3' if model is not provided
    return Response(stream_response(user_message, model), mimetype='text/event-stream')

@app.route('/api/rag_search', methods=['POST'])
def rag_search():
    data = request.json
    database_name = data.get('database_name')
    user_message = data.get('message')
    model = data.get('model', 'llama3')  # Default to 'llama3' if model is not provided
    if not database_name or not user_message:
        return jsonify({"response": "Error: Please provide both database name and user message."}), 400

    document = retrieve_document(database_name, user_message)
    return jsonify({"document": document, "model": model}), 200

@app.route('/api/document_query', methods=['GET'])
def document_query():
    document_text = request.args.get('document_text')
    user_query = request.args.get('query')
    model = request.args.get('model', 'llama3')  # Default to 'llama3' if model is not provided
    if not document_text or not user_query:
        return jsonify({"response": "Error: Please provide both document text and query."}), 400

    response_generator = rag_response(user_query, document_text, model)
    return Response(response_generator, mimetype='text/event-stream')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        document_text = extract_text_from_pdf(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({"message": "File uploaded successfully", "document_text": document_text, "filename": filename}), 200
    return jsonify({"error": "Invalid file type"}), 400

@app.route('/api/documents', methods=['GET'])
def list_documents():
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if allowed_file(f)]
    return jsonify(files), 200

@app.route('/api/document/<filename>', methods=['GET'])
def get_document(filename):
    if allowed_file(filename):
        document_text = extract_text_from_pdf(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({"document_text": document_text}), 200
    return jsonify({"error": "Invalid file type"}), 400

@app.route('/api/pdf_query', methods=['GET'])
def pdf_query():
    user_message = request.args.get('query')
    document_text = request.args.get('document_text')
    model = request.args.get('model', 'llama3')  # Default to 'llama3' if model is not provided
    if not user_message or not document_text:
        return jsonify({"response": "Error: Please provide both user message and document text."}), 400

    response_generator = infer_context_from_pdf(document_text, user_message, model)
    return Response(response_generator, mimetype='text/event-stream')

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True, port=5001)
