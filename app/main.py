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
    response = requests.post(GRAPHDB_ENDPOINT, data=sparql_query, headers=headers)
    response.raise_for_status()
    return response.json()


# Helper function to extract the filename from a URI
def extract_filename(uri):
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
    SELECT ?image ?next_player ?white_pieces ?black_pieces
           ?white_kings ?white_queens ?white_rooks ?white_bishops ?white_knights ?white_pawns
           ?black_kings ?black_queens ?black_rooks ?black_bishops ?black_knights ?black_pawns
           ?white_castling_kingside ?white_castling_queenside
           ?black_castling_kingside ?black_castling_queenside
           ?en_passant_white ?en_passant_black
    WHERE {{
        ?image chess:next_player ?next_player .
        ?image chess:white_pieces ?white_pieces .
        ?image chess:black_pieces ?black_pieces .

        OPTIONAL {{ ?white_pieces chess:white_pieces_kings ?white_kings . }}
        OPTIONAL {{ ?white_pieces chess:white_pieces_queens ?white_queens . }}
        OPTIONAL {{ ?white_pieces chess:white_pieces_rooks ?white_rooks . }}
        OPTIONAL {{ ?white_pieces chess:white_pieces_bishops ?white_bishops . }}
        OPTIONAL {{ ?white_pieces chess:white_pieces_knights ?white_knights . }}
        OPTIONAL {{ ?white_pieces chess:white_pieces_pawns ?white_pawns . }}

        OPTIONAL {{ ?black_pieces chess:black_pieces_kings ?black_kings . }}
        OPTIONAL {{ ?black_pieces chess:black_pieces_queens ?black_queens . }}
        OPTIONAL {{ ?black_pieces chess:black_pieces_rooks ?black_rooks . }}
        OPTIONAL {{ ?black_pieces chess:black_pieces_bishops ?black_bishops . }}
        OPTIONAL {{ ?black_pieces chess:black_pieces_knights ?black_knights . }}
        OPTIONAL {{ ?black_pieces chess:black_pieces_pawns ?black_pawns . }}

        OPTIONAL {{ ?image chess:white_castling_kingside ?white_castling_kingside . }}
        OPTIONAL {{ ?image chess:white_castling_queenside ?white_castling_queenside . }}
        OPTIONAL {{ ?image chess:black_castling_kingside ?black_castling_kingside . }}
        OPTIONAL {{ ?image chess:black_castling_queenside ?black_castling_queenside . }}

        OPTIONAL {{ ?image chess:en_passant_white ?en_passant_white . }}
        OPTIONAL {{ ?image chess:en_passant_black ?en_passant_black . }}

        {' '.join(piece_conditions)}
    }}
    """

    try:
        results = query_graphdb(sparql_query)

        chess_boards = []
        for index, binding in enumerate(results["results"]["bindings"]):
            chess_boards.append({
                "index": index + 1,
                "filename": extract_filename(binding["image"]["value"]),
                "next_player": binding.get("next_player", {}).get("value", ""),
                "white_pieces": {
                    "kings": binding.get("white_kings", {}).get("value", "0"),
                    "queens": binding.get("white_queens", {}).get("value", "0"),
                    "rooks": binding.get("white_rooks", {}).get("value", "0"),
                    "bishops": binding.get("white_bishops", {}).get("value", "0"),
                    "knights": binding.get("white_knights", {}).get("value", "0"),
                    "pawns": binding.get("white_pawns", {}).get("value", "0"),
                },
                "black_pieces": {
                    "kings": binding.get("black_kings", {}).get("value", "0"),
                    "queens": binding.get("black_queens", {}).get("value", "0"),
                    "rooks": binding.get("black_rooks", {}).get("value", "0"),
                    "bishops": binding.get("black_bishops", {}).get("value", "0"),
                    "knights": binding.get("black_knights", {}).get("value", "0"),
                    "pawns": binding.get("black_pawns", {}).get("value", "0"),
                },
                "castling": {
                    "white_kingside": binding.get("white_castling_kingside", {}).get("value", "false"),
                    "white_queenside": binding.get("white_castling_queenside", {}).get("value", "false"),
                    "black_kingside": binding.get("black_castling_kingside", {}).get("value", "false"),
                    "black_queenside": binding.get("black_castling_queenside", {}).get("value", "false"),
                },
                "en_passant": {
                    "white": binding.get("en_passant_white", {}).get("value", "false"),
                    "black": binding.get("en_passant_black", {}).get("value", "false"),
                }
            })

        return jsonify(chess_boards)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/filter", methods=["POST"])
def filter():
    """
    Filter endpoint to query chess boards based on piece counts for the next player.
    Example Input JSON: {"rooks": 2, "queens": 1}
    """
    filters = request.json
    if not filters:
        return jsonify({"error": "No filters provided"}), 400

    # Build SPARQL query dynamically
    conditions = []
    piece_conditions = []

    # Base SPARQL query to determine the next player
    sparql_query = """
    PREFIX chess: <http://imaginealpacas.org/chess/>
    SELECT ?image ?next_player ?white_kings ?white_queens ?white_rooks ?white_bishops ?white_knights ?white_pawns
        ?black_kings ?black_queens ?black_rooks ?black_bishops ?black_knights ?black_pawns
    WHERE {
        ?image chess:next_player ?next_player .
        ?image chess:white_pieces ?white_pieces .
        ?image chess:black_pieces ?black_pieces .
    """

    # Dynamically add conditions for the selected pieces
    for piece, count in filters.items():
        if count is not None:
            piece_conditions.append(
                f"""
                OPTIONAL {{
                    ?white_pieces chess:white_pieces_{piece} ?white_{piece} .
                    ?black_pieces chess:black_pieces_{piece} ?black_{piece} .
                }}
                FILTER (
                    (?next_player = "white" && ?white_{piece} = {count})
                    ||
                    (?next_player = "black" && ?black_{piece} = {count})
                )
                """
            )

    # Combine the conditions
    sparql_query += " ".join(piece_conditions) + "\n}"

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
        for idx, binding in enumerate(results["results"]["bindings"]):
            image_data = {
                "index": idx + 1,
                "filename": binding["image"]["value"].split('/')[-1],
                "next_player": binding["next_player"]["value"],
                "white_pieces": {
                    "kings": binding.get("white_kings", {}).get("value", "0"),
                    "queens": binding.get("white_queens", {}).get("value", "0"),
                    "rooks": binding.get("white_rooks", {}).get("value", "0"),
                    "bishops": binding.get("white_bishops", {}).get("value", "0"),
                    "knights": binding.get("white_knights", {}).get("value", "0"),
                    "pawns": binding.get("white_pawns", {}).get("value", "0"),
                },
                "black_pieces": {
                    "kings": binding.get("black_kings", {}).get("value", "0"),
                    "queens": binding.get("black_queens", {}).get("value", "0"),
                    "rooks": binding.get("black_rooks", {}).get("value", "0"),
                    "bishops": binding.get("black_bishops", {}).get("value", "0"),
                    "knights": binding.get("black_knights", {}).get("value", "0"),
                    "pawns": binding.get("black_pawns", {}).get("value", "0"),
                },
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


@app.route("/initial", methods=["GET"])
def get_initial_images():
    """
    Fetches the first 4 chess puzzles from the RDF dataset with puzzle ID.
    """
    sparql_query = """
    PREFIX chess: <http://imaginealpacas.org/chess/>
    SELECT ?image ?puzzle_id
    WHERE {
        ?image chess:puzzle_id ?puzzle_id .
    }
    ORDER BY ASC(xsd:integer(?puzzle_id))
    LIMIT 6
    """

    try:
        results = query_graphdb(sparql_query)

        chess_puzzles = []
        for index, binding in enumerate(results["results"]["bindings"]):
            chess_puzzles.append({
                "index": index + 1,
                "filename": extract_filename(binding["image"]["value"]),
                "puzzle_id": binding.get("puzzle_id", {}).get("value", "N/A"),
            })

        return jsonify(chess_puzzles)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
