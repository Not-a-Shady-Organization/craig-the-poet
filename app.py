from flask import Flask, request
from craig_the_poet import poem_stitcher
import os
import traceback

app = Flask(__name__)

@app.route('/',  methods=['GET'])
def hello_world():
    return 'Craig, the Poet is live :)'

@app.route('/', methods=['POST'])
def kickoff_poem_stitcher():
    data = request.get_json()
    try:
        return str(poem_stitcher(**data))
    except Exception as e:
        tb = traceback.format_exc()
        return f'Exception occurred: {e}\n{tb}'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
