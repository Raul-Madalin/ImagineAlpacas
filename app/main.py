import os
from flask import Flask, abort, request, jsonify, send_from_directory
from flask_cors import CORS
from rdflib import Graph
from urllib.parse import urlparse
import requests

app = Flask(__name__)
CORS(app)
GRAPHDB_ENDPOINT = "http://localhost:7200/repositories/chess-test-repo"

def query_graphdb(sparql_query):
    """
    Sends a SPARQL query to the GraphDB repository.
    """
    headers = {
        "Content-Type": "application/sparql-query",
        "Accept": "application/json"
    }
    response = request.post(GRAPHDB_ENDPOINT, data=sparql_query, headers=headers)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()


# Helper function to extract the filename from a URI
def extract_filename(uri):
    # Parse the URI and return the last part as the filename
    return os.path.basename(urlparse(uri).path)

@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    piece_conditions = []
    piece_mapping = {
        "pawns": ("chess:white_pieces_pawns", "chess:black_pieces_pawns"),
        "rooks": ("chess:white_pieces_rooks", "chess:black_pieces_rooks"),
        "queens": ("chess:white_pieces_queens", "chess:black_pieces_queens"),
        "bishops": ("chess:white_pieces_bishops", "chess:black_pieces_bishops"),
        "knights": ("chess:white_pieces_knights", "chess:black_pieces_knights")
    }

    for piece in query.split():
        if piece.lower() in piece_mapping:
            white_piece, black_piece = piece_mapping[piece.lower()]
            piece_conditions.append(f"""
                OPTIONAL {{ ?white_pieces {white_piece} ?white_value . }}
                OPTIONAL {{ ?black_pieces {black_piece} ?black_value . }}
                FILTER (
                    (?next_player = "white" && bound(?white_value) && ?white_value > 0)
                    || 
                    (?next_player = "black" && bound(?black_value) && ?black_value > 0)
                )
            """)

    sparql_query = f"""
    PREFIX chess: <http://imaginealpacas.org/chess/>
    SELECT ?image WHERE {{
        ?image chess:next_player ?next_player .
        ?image chess:white_pieces ?white_pieces .
        ?image chess:black_pieces ?black_pieces .
        {' '.join(piece_conditions)}
    }}
    """

    try:
        headers = {
            "Content-Type": "application/sparql-query",
            "Accept": "application/json"
        }
        response = requests.post(GRAPHDB_ENDPOINT, data=sparql_query, headers=headers)
        response.raise_for_status()  # Raise error for bad HTTP responses

        results = response.json()

        images = [extract_filename(binding["image"]["value"]) for binding in results["results"]["bindings"]]

        return jsonify(images)

    except Exception as e:
        print("\n❌ Debug: Error occurred:\n", str(e))
        return jsonify({"error": str(e)}), 500



import requests
# TODO: Adapt the filter endpoint to new improved RDF schema
@app.route("/filter", methods=["POST"])
def filter():
    """
    Filter endpoint to query chess boards based on metadata properties.
    Example Input JSON: {"pawns": ">2", "rooks": "=1"}
    """
    filters = request.json
    if not filters:
        return jsonify({"error": "No filters provided"}), 400

    # Build SPARQL query dynamically
    conditions = []
    for key, condition in filters.items():
        if condition:
            print(key, condition[0], condition[1:])
            operator = condition[0]  # Extract operator (e.g., '=', '>', '<')
            value = condition[1:]    # Extract value (e.g., '1', '2')
            conditions.append(f"?image <http://imaginealpacas.org/chess/{key}> ?{key} . FILTER (?{key} {operator} {value})")

    sparql_query = f"""
    PREFIX chess: <http://imaginealpacas.org/chess/>
    SELECT ?image ?white_pieces ?p ?r ?q ?b ?n WHERE {{
        ?image chess:white_pieces ?white_pieces .
        ?white_pieces chess:white_pieces_pawns ?p .
        ?white_pieces chess:white_pieces_rooks ?r .
        ?white_pieces chess:white_pieces_queens ?q .
        ?white_pieces chess:white_pieces_bishops ?b .
        ?white_pieces chess:white_pieces_knights ?n .
        {" ".join(conditions)}
    }}
    """

    try:
        # Send the SPARQL query to GraphDB
        headers = {
            "Content-Type": "application/sparql-query",
            "Accept": "application/json"
        }
        response = requests.post(GRAPHDB_ENDPOINT, data=sparql_query, headers=headers)
        response.raise_for_status()

        # Parse the results from GraphDB
        results = response.json()
        images = []
        for binding in results["results"]["bindings"]:
            image_data = {
                "filename": binding["image"]["value"].split('/')[-1],  # Extract just the filename
                "pawns": binding["p"]["value"],
                "rooks": binding["r"]["value"],
                "queens": binding["q"]["value"],
                "bishops": binding["b"]["value"],
                "knights": binding["n"]["value"],
            }
            images.append(image_data)

        return jsonify(images)
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/images/<filename>')
def serve_image(filename):
    print(f"Requested image: {filename}")
    path = os.path.dirname(os.path.dirname(__file__))
    # Try to find the file in both directories
    if os.path.exists(f'{path}/dataset/test/{filename}'):
        return send_from_directory(f'{path}/dataset/test/', filename)
    elif os.path.exists(f'{path}/dataset/train/{filename}'):
        return send_from_directory(f'{path}/dataset/train/', filename)
    else:
        abort(404)  # File not found


if __name__ == "__main__":
    app.run(debug=True)
