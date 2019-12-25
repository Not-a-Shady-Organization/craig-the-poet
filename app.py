from flask import Flask, request
from poem_stitcher import poem_stitcher
import os

app = Flask(__name__)

@app.route('/',  methods=['GET'])
def hello_world():
    return 'Poem Stitcher is live :)'

@app.route('/', methods=['POST'])
def kickoff_poem_stitcher():
    data = request.get_json()
    try:
        return str(poem_stitcher(**data))
    except Exception as e:
        return f'Exception occurred: {e}'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
