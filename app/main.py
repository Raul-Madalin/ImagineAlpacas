import os
from flask import Flask, abort, request, jsonify, send_from_directory
from flask_cors import CORS
from rdflib import Graph
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

path = os.path.dirname(os.path.dirname(__file__))
# path = os.path.dirname(path)
rdf_file_path = os.path.join(path, 'ontology.rdf')
g = Graph()
g.parse(rdf_file_path, format="xml")

# Helper function to extract the filename from a URI
def extract_filename(uri):
    # Parse the URI and return the last part as the filename
    return os.path.basename(urlparse(uri).path)

@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    # Build SPARQL query to find images matching the query
    pieces = query.split()
    sparql_query = """
    SELECT ?image ?p ?r ?q ?b ?n WHERE {
        ?image <http://example.org/chess/pawns> ?p .
        ?image <http://example.org/chess/rooks> ?r .
        ?image <http://example.org/chess/queens> ?q .
        ?image <http://example.org/chess/bishops> ?b .
        ?image <http://example.org/chess/knights> ?n .
        # Additional conditions can be added dynamically
    }
    """
    
    # Execute the SPARQL query
    results = g.query(sparql_query)

    # Extract results into JSON format
    images = []
    for row in results:
        image_data = {
            "filename": extract_filename(str(row[0])),
            "pawns": str(row[1]),
            "rooks": str(row[2]),
            "queens": str(row[3]),
            "bishops": str(row[4]),
            "knights": str(row[5]),
        }
        images.append(image_data)

    return jsonify(images)


@app.route("/filter", methods=["POST"])
def filter():
    filters = request.json
    if not filters:
        return jsonify({"error": "No filters provided"}), 400

    # Build dynamic SPARQL query
    sparql_query = "SELECT ?image WHERE {\n"
    conditions = []
    for key, condition in filters.items():
        operator = condition[0]  # Extract operator (e.g., '=', '>', '<')
        value = condition[1:]  # Extract value (e.g., '1', '2')
        conditions.append(f"?image <http://example.org/chess/{key}> ?{key} .\nFILTER (?{key} {operator} {value})")

    sparql_query += "\n".join(conditions) + "\n}"
    
    print("Generated SPARQL Query:\n", sparql_query)  # Debugging: Print the query

    # Execute query
    results = g.query(sparql_query)
    filenames = [extract_filename(str(row[0])) for row in results]  # Extract only filenames
    return jsonify(filenames)


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