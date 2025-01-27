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

    # Extract pieces from the query
    pieces = query.split()
    piece_conditions = []
    
    # Map piece names to RDF property URIs
    piece_mapping = {
        "pawns": "http://example.org/chess/pawns",
        "rooks": "http://example.org/chess/rooks",
        "queens": "http://example.org/chess/queens",
        "bishops": "http://example.org/chess/bishops",
        "knights": "http://example.org/chess/knights"
    }

    # Dynamically construct SPARQL conditions for the requested pieces
    for piece in pieces:
        piece_uri = piece_mapping.get(piece.lower())
        if piece_uri:
            piece_conditions.append(f"?image <{piece_uri}> ?{piece.lower()} . FILTER (?{piece.lower()} > 0)")

    # Combine conditions into the SPARQL query
    sparql_query = f"""
    PREFIX ex: <http://example.org/chess/>
    SELECT ?image ?p ?r ?q ?b ?n WHERE {{
        ?image ex:pawns ?p .
        ?image ex:rooks ?r .
        ?image ex:queens ?q .
        ?image ex:bishops ?b .
        ?image ex:knights ?n .
        {' '.join(piece_conditions)}
    }}
    """
    
    try:
        # Send the SPARQL query to GraphDB
        headers = {
            "Content-Type": "application/sparql-query",
            "Accept": "application/json"
        }
        response = requests.post(GRAPHDB_ENDPOINT, data=sparql_query, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses

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


import requests

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
            conditions.append(f"?image <http://example.org/chess/{key}> ?{key} . FILTER (?{key} {operator} {value})")

    sparql_query = f"""
    PREFIX ex: <http://example.org/chess/>
    SELECT ?image ?p ?r ?q ?b ?n WHERE {{
        ?image ex:pawns ?p .
        ?image ex:rooks ?r .
        ?image ex:queens ?q .
        ?image ex:bishops ?b .
        ?image ex:knights ?n .
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
