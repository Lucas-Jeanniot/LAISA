from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from inference import stream_response

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

if __name__ == '__main__':
    app.run(debug=True, port=5001)
