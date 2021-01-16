from flask import Flask, request, render_template, jsonify
from wiki_passage_retriever.retrieve import get_most_relevant_passages
from wiki_passage_retriever.index import index_wikipedia, retrieve_by_index
import uuid
import json
import sqlite3


DATABASE_NAME = "wikipedia_index.db"
app = Flask(__name__)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/retrieve', methods=['GET'])
def retrieve():
    question = request.args.get('question')
    query = request.args.get('query')
    topk = int(request.args.get("topk"))

    print(question, query, topk)  # for debugging

    # check if the query has already been indexed:
    with sqlite3.connect(DATABASE_NAME) as conn:
        conn.execute("SELECT index_dir_path FROM wikipedia_index WHERE query=?", [query])
        rows = conn.cursor().fetchall()

        for row in rows:
            # since query is unique, there should be at most one row
            return jsonify(result=retrieve_by_index(row[0], question))
        else:
            # query was not indexed:
            return jsonify(result=get_most_relevant_passages(query, question, topk))


@app.route('/index', methods=['POST'])
def index():
    query = request.args.get('query')
    index_dir_path = str(uuid.uuid4())  # randomize a name to store queries
    index_wikipedia(query, index_dir_path)

    # Inserts metadata to database:
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        sql_query = "INSERT INTO wikipedia_index(query_name, index_dir_path) VALUES(?, ?);"
        cursor.execute(sql_query, [query, index_dir_path])
        conn.commit()

    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


if __name__ == '__main__':
    app.run(debug=False)
