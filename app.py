from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['github_events']
collection = db['events']

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.json
    event_type = request.headers.get('X-GitHub-Event')

    if event_type == 'push':
        data = {
            'author': payload['pusher']['name'],
            'to_branch': payload['ref'].split('/')[-1],
            'timestamp': datetime.utcnow().strftime('%d %B %Y - %I:%M %p UTC'),
            'type': 'push'
        }

    elif event_type == 'pull_request':
        action = payload['action']
        if action in ['opened', 'reopened']:
            data = {
                'author': payload['pull_request']['user']['login'],
                'from_branch': payload['pull_request']['head']['ref'],
                'to_branch': payload['pull_request']['base']['ref'],
                'timestamp': datetime.utcnow().strftime('%d %B %Y - %I:%M %p UTC'),
                'type': 'pull_request'
            }
        elif action == 'closed' and payload['pull_request']['merged']:
            data = {
                'author': payload['pull_request']['user']['login'],
                'from_branch': payload['pull_request']['head']['ref'],
                'to_branch': payload['pull_request']['base']['ref'],
                'timestamp': datetime.utcnow().strftime('%d %B %Y - %I:%M %p UTC'),
                'type': 'merge'
            }
        else:
            return jsonify({'message': 'PR ignored'}), 200
    else:
        return jsonify({'message': 'Unhandled event'}), 200

    collection.insert_one(data)
    return jsonify({'message': 'Saved'}), 200

@app.route('/events', methods=['GET'])
def get_events():
    data = list(collection.find({}, {'_id': 0}))
    return jsonify(data)

if __name__ == '__main__':
    app.run()
