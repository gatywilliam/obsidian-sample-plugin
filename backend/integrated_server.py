from haystack import Document
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.embedders import SentenceTransformersTextEmbedder, SentenceTransformersDocumentEmbedder
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
import docs_folder
from haystack import Pipeline
import os
import haystack_api
from flask import Flask, Response, request, send_file, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS, cross_origin
import socketio

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
sio = socketio.Client()

socket_io = SocketIO(app, cors_allowed_origins="*", logger=True)
socket_io.init_app(app, cors_allowed_origins="*")

RESULTS = None
QUERY = None
CONTINUE_RUNNING = True
QUERY_PIPELINE = Pipeline()
EMBEDDINGS_MADE = False
NUM_RESULTS = 3

@app.route('/embeddings_status', methods=['GET'])
def check_embeddings():
    global EMBEDDINGS_MADE
    print(str(EMBEDDINGS_MADE))
    return jsonify({"embeddings_status": str(EMBEDDINGS_MADE).lower()})

@app.route('/run_startup', methods=['POST'])
def run_startup():
    document_store = InMemoryDocumentStore(embedding_similarity_function="cosine")

    path = request.get_json(force=True).get('path')

    # path = os.path.join(os.getcwd(), "docs") #TODO replace

    documents_read = docs_folder.get_files_in_folder(path)

    documents = [Document(content=document) for document in documents_read]

    document_embedder = SentenceTransformersDocumentEmbedder(
        model="BAAI/bge-large-en-v1.5")
    document_embedder.warm_up()

    documents_with_embeddings = document_embedder.run(documents)["documents"]

    document_store.write_documents(documents_with_embeddings)

    QUERY_PIPELINE.add_component("text_embedder", SentenceTransformersTextEmbedder(model="BAAI/bge-large-en-v1.5"))
    QUERY_PIPELINE.add_component("retriever", InMemoryEmbeddingRetriever(document_store=document_store))
    QUERY_PIPELINE.connect("text_embedder.embedding", "retriever.query_embedding")
    global EMBEDDINGS_MADE
    EMBEDDINGS_MADE = True
    print(EMBEDDINGS_MADE)
    return 'Success'

@app.route('/get_query', methods=['POST'])
def get_query():
    global QUERY
    QUERY = request.get_json(force=True).get('input').lower()
    global RESULTS
    RESULTS = QUERY_PIPELINE.run({"text_embedder": {"text": QUERY}})
    return 'Success'

@app.route('/return_results', methods=['GET'])
def return_results():
    global RESULTS
    global NUM_RESULTS
    docs = RESULTS["retriever"]["documents"]
    query_results = []
    for i in range(NUM_RESULTS):
        print(docs[i])
        #"title": docs[i].meta["name"], 
        query_results.append({"content": docs[i].content})
    json = {"results": query_results}
    # json = {"results": RESULTS["retriever"]["documents"][:3]}
    return jsonify(json)

@app.route('/continue_running', methods=['POST'])
def continue_running():
    if request.get_json(force=True).get('input').lower() == "false":
        socket_io.stop()
        global CONTINUE_RUNNING
        CONTINUE_RUNNING = False
    return 'Success'

if __name__ == "__main__":
    print("server started")
    socket_io.run(app, host='0.0.0.0', port=5000, debug=True)
