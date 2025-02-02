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
    query = request.args.get("query", "").strip().lower()
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    query_terms = query.split()  # Split the query into terms like ["rooks", "queen"]

    # Prepare SPARQL conditions for each piece type
    conditions = []
    for term in query_terms:
        is_plural = term.endswith("s")
        if not is_plural:
            term = term + "s"

        conditions.append(f"""
            FILTER (
                (?next_player = "white" && bound(?white_{term}) && ?white_{term} {"=" if not is_plural else ">"} 1)
                ||
                (?next_player = "black" && bound(?black_{term}) && ?black_{term} {"=" if not is_plural else ">"} 1)
            )
        """)

    sparql_query = f"""
    PREFIX chess: <http://imaginealpacas.org/chess/>
    SELECT ?image ?puzzle_id ?next_player ?white_kings ?white_queens ?white_rooks ?white_bishops ?white_knights ?white_pawns
           ?black_kings ?black_queens ?black_rooks ?black_bishops ?black_knights ?black_pawns
           ?white_castling_kingside ?white_castling_queenside
           ?black_castling_kingside ?black_castling_queenside
           ?en_passant_white ?en_passant_black
    WHERE {{
        ?image chess:puzzle_id ?puzzle_id .
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

        {" ".join(conditions)}
    }}
    ORDER BY ASC(xsd:integer(?puzzle_id))
    """

    try:
        results = query_graphdb(sparql_query)

        chess_boards = []
        for index, binding in enumerate(results["results"]["bindings"]):
            chess_boards.append({
                "index": index + 1,
                "filename": extract_filename(binding["image"]["value"]),
                "puzzle_id": binding.get("puzzle_id", {}).get("value", "N/A"),
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
    Example Input JSON: {"rooks": [0, 1], "queens": [2+]}
    """
    data = request.json
    filters = data.get("filters", {})
    puzzle_ids = data.get("puzzle_ids", [])

    if not filters or not puzzle_ids:
        return jsonify({"error": "Filters and puzzle IDs are required"}), 400
    
    game_state_filters = filters.pop("game_state", None)
    
    if game_state_filters is None or len(game_state_filters) == 0:
        sparql_query = """
        PREFIX chess: <http://imaginealpacas.org/chess/>
        SELECT ?image ?puzzle_id ?next_player 
            ?white_kings ?white_queens ?white_rooks ?white_bishops ?white_knights ?white_pawns
            ?black_kings ?black_queens ?black_rooks ?black_bishops ?black_knights ?black_pawns
        WHERE {
            ?image chess:puzzle_id ?puzzle_id .
            ?image chess:next_player ?next_player .
            ?image chess:white_pieces ?white_pieces .
            ?image chess:black_pieces ?black_pieces .

            OPTIONAL { ?white_pieces chess:white_pieces_kings ?white_kings . }
            OPTIONAL { ?white_pieces chess:white_pieces_queens ?white_queens . }
            OPTIONAL { ?white_pieces chess:white_pieces_rooks ?white_rooks . }
            OPTIONAL { ?white_pieces chess:white_pieces_bishops ?white_bishops . }
            OPTIONAL { ?white_pieces chess:white_pieces_knights ?white_knights . }
            OPTIONAL { ?white_pieces chess:white_pieces_pawns ?white_pawns . }

            OPTIONAL { ?black_pieces chess:black_pieces_kings ?black_kings . }
            OPTIONAL { ?black_pieces chess:black_pieces_queens ?black_queens . }
            OPTIONAL { ?black_pieces chess:black_pieces_rooks ?black_rooks . }
            OPTIONAL { ?black_pieces chess:black_pieces_bishops ?black_bishops . }
            OPTIONAL { ?black_pieces chess:black_pieces_knights ?black_knights . }
            OPTIONAL { ?black_pieces chess:black_pieces_pawns ?black_pawns . }
        """
    else:
        sparql_query = """
        PREFIX chess: <http://imaginealpacas.org/chess/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

        SELECT 
        ?image ?puzzle_id ?next_player
        ?white_kings ?white_queens ?white_rooks ?white_bishops ?white_knights ?white_pawns
        ?black_kings ?black_queens ?black_rooks ?black_bishops ?black_knights ?black_pawns
        ?total_pieces 
        ?computed_state
        WHERE {
        ?image chess:puzzle_id ?puzzle_id .
        ?image chess:next_player ?next_player .
        ?image chess:white_pieces ?white_pieces .
        ?image chess:black_pieces ?black_pieces .

        OPTIONAL { ?white_pieces chess:white_pieces_kings ?white_kings . }
        OPTIONAL { ?white_pieces chess:white_pieces_queens ?white_queens . }
        OPTIONAL { ?white_pieces chess:white_pieces_rooks ?white_rooks . }
        OPTIONAL { ?white_pieces chess:white_pieces_bishops ?white_bishops . }
        OPTIONAL { ?white_pieces chess:white_pieces_knights ?white_knights . }
        OPTIONAL { ?white_pieces chess:white_pieces_pawns ?white_pawns . }

        OPTIONAL { ?black_pieces chess:black_pieces_kings ?black_kings . }
        OPTIONAL { ?black_pieces chess:black_pieces_queens ?black_queens . }
        OPTIONAL { ?black_pieces chess:black_pieces_rooks ?black_rooks . }
        OPTIONAL { ?black_pieces chess:black_pieces_bishops ?black_bishops . }
        OPTIONAL { ?black_pieces chess:black_pieces_knights ?black_knights . }
        OPTIONAL { ?black_pieces chess:black_pieces_pawns ?black_pawns . }

        # 1) Sum all pieces
        BIND(
            (
            COALESCE(xsd:integer(?white_kings), 0) +
            COALESCE(xsd:integer(?white_queens), 0) +
            COALESCE(xsd:integer(?white_rooks), 0) +
            COALESCE(xsd:integer(?white_bishops), 0) +
            COALESCE(xsd:integer(?white_knights), 0) +
            COALESCE(xsd:integer(?white_pawns), 0) +
            COALESCE(xsd:integer(?black_kings), 0) +
            COALESCE(xsd:integer(?black_queens), 0) +
            COALESCE(xsd:integer(?black_rooks), 0) +
            COALESCE(xsd:integer(?black_bishops), 0) +
            COALESCE(xsd:integer(?black_knights), 0) +
            COALESCE(xsd:integer(?black_pawns), 0)
            )
            AS ?total_pieces
        )

        # 2) Classify ?total_pieces => ?computed_state
        BIND(
            IF(
            ?total_pieces >= 24,
            "opening",
            IF(
                ?total_pieces >= 14,
                "midgame",
                "endgame"
            )
            )
            AS ?computed_state
        )
        """

    # Restrict to only puzzles currently displayed
    puzzle_id_list = ", ".join(map(str, puzzle_ids))
    sparql_query += f" FILTER (?puzzle_id IN ({puzzle_id_list})) "

    # Convert filters into SPARQL conditions
    piece_conditions = []
    for piece, values in filters.items():
        if len(values) > 0:
            conditions = []
            for value in values:
                if value == "3+":
                    conditions.append(f"(?next_player = \"white\" && ?white_{piece} >= 3) || (?next_player = \"black\" && ?black_{piece} >= 3)")
                elif value == "2+":
                    conditions.append(f"(?next_player = \"white\" && ?white_{piece} >= 2) || (?next_player = \"black\" && ?black_{piece} >= 2)")
                elif value == "9+":
                    conditions.append(f"(?next_player = \"white\" && ?white_{piece} >= 9) || (?next_player = \"black\" && ?black_{piece} >= 9)")
                else:
                    conditions.append(f"(?next_player = \"white\" && ?white_{piece} = {value}) || (?next_player = \"black\" && ?black_{piece} = {value})")
            
            piece_conditions.append(f"FILTER ({' || '.join(conditions)})")

    # Append conditions to the SPARQL query
    if piece_conditions:
        sparql_query += " ".join(piece_conditions)

    if game_state_filters:
        # e.g. ["opening","midgame","endgame"]
        states_str = ", ".join(f'\"{s}\"' for s in game_state_filters)
        sparql_query += f"\nFILTER(?computed_state IN ({states_str}))"

    sparql_query += "\n}ORDER BY ASC(xsd:integer(?puzzle_id))"

    print(sparql_query)

    try:
        # Send SPARQL query to GraphDB
        results = query_graphdb(sparql_query)

        # Process query results
        filtered_puzzles = []
        for index, binding in enumerate(results["results"]["bindings"]):
            filtered_puzzles.append({
                "index": index + 1,
                "filename": extract_filename(binding["image"]["value"]),
                "puzzle_id": binding.get("puzzle_id", {}).get("value", "N/A"),
                "next_player": binding.get("next_player", {}).get("value", ""),
                "game_state": binding.get("computed_state", {}).get("value", "unknown"),
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
            })

        return jsonify(filtered_puzzles)

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
    Fetches the first 3 chess puzzles from the RDF dataset with puzzle ID.
    """
    sparql_query = """
    PREFIX chess: <http://imaginealpacas.org/chess/>
    SELECT ?image ?puzzle_id
    WHERE {
        ?image chess:puzzle_id ?puzzle_id .
    }
    ORDER BY ASC(xsd:integer(?puzzle_id))
    # LIMIT 6
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
    

@app.route("/rdf-recommendations", methods=["POST"])
def get_recommendations():
    """
    Fetches the best 3 recommended chess puzzles based on normalized similarity.
    """
    data = request.json
    displayed_puzzle_ids = data.get("puzzle_ids", [])

    print(displayed_puzzle_ids)

    if not displayed_puzzle_ids:
        return jsonify({"error": "Displayed puzzle IDs are required"}), 400

    puzzle_id_conditions = ", ".join([f'{pid}' for pid in displayed_puzzle_ids])

    # Query to analyze displayed puzzles
    displayed_query = f"""
    PREFIX chess: <http://imaginealpacas.org/chess/>
    SELECT (COUNT(?puzzle) AS ?total_puzzles)
           (SUM(IF((?next_player = "white" && (?white_castling_kingside = true || ?white_castling_queenside = true)) ||
                   (?next_player = "black" && (?black_castling_kingside = true || ?black_castling_queenside = true)), 1, 0)) AS ?has_castling)
           (SUM(IF((?next_player = "white" && ?en_passant_white = true) ||
                   (?next_player = "black" && ?en_passant_black = true), 1, 0)) AS ?has_en_passant)
           (SUM(IF(?next_player = "white", ?white_pieces_queens, ?black_pieces_queens)) AS ?queens)
           (SUM(IF(?next_player = "white", ?white_pieces_rooks, ?black_pieces_rooks)) AS ?rooks)
           (SUM(IF(?next_player = "white", ?white_pieces_bishops, ?black_pieces_bishops)) AS ?bishops)
           (SUM(IF(?next_player = "white", ?white_pieces_knights, ?black_pieces_knights)) AS ?knights)
           (SUM(IF(?next_player = "white", ?white_pieces_pawns, ?black_pieces_pawns)) AS ?pawns)
    WHERE {{
        ?puzzle chess:puzzle_id ?puzzle_id .
        ?puzzle chess:next_player ?next_player .

        OPTIONAL {{ ?puzzle chess:white_castling_kingside ?white_castling_kingside . }}
        OPTIONAL {{ ?puzzle chess:white_castling_queenside ?white_castling_queenside . }}
        OPTIONAL {{ ?puzzle chess:black_castling_kingside ?black_castling_kingside . }}
        OPTIONAL {{ ?puzzle chess:black_castling_queenside ?black_castling_queenside . }}

        OPTIONAL {{ ?puzzle chess:en_passant_white ?en_passant_white . }}
        OPTIONAL {{ ?puzzle chess:en_passant_black ?en_passant_black . }}

        OPTIONAL {{ ?puzzle chess:white_pieces ?white_pieces .
                   ?white_pieces chess:white_pieces_queens ?white_pieces_queens .
                   ?white_pieces chess:white_pieces_rooks ?white_pieces_rooks .
                   ?white_pieces chess:white_pieces_bishops ?white_pieces_bishops .
                   ?white_pieces chess:white_pieces_knights ?white_pieces_knights .
                   ?white_pieces chess:white_pieces_pawns ?white_pieces_pawns .
        }}
        OPTIONAL {{ ?puzzle chess:black_pieces ?black_pieces .
                   ?black_pieces chess:black_pieces_queens ?black_pieces_queens .
                   ?black_pieces chess:black_pieces_rooks ?black_pieces_rooks .
                   ?black_pieces chess:black_pieces_bishops ?black_pieces_bishops .
                   ?black_pieces chess:black_pieces_knights ?black_pieces_knights .
                   ?black_pieces chess:black_pieces_pawns ?black_pieces_pawns .
        }}

        FILTER (?puzzle_id IN ({puzzle_id_conditions}))
    }}
    """

    try:
        displayed_results = query_graphdb(displayed_query)

        # If no puzzles were found, return an empty list
        if "results" not in displayed_results or not displayed_results["results"]["bindings"]:
            return jsonify([])

        # Extract feature counts
        feature_counts = displayed_results["results"]["bindings"][0]

        # Normalization factors
        max_values = {
            "has_castling": 1, "has_en_passant": 1,
            "queens": 9, "rooks": 10, "bishops": 10, "knights": 10, "pawns": 8
        }

        # Normalize the counts
        normalized_scores = {
            feature: (int(feature_counts[feature]["value"]) / max_values[feature])
            for feature in max_values
        }

        # Determine the most dominant characteristic (highest normalized score)
        dominant_feature = max(normalized_scores, key=normalized_scores.get)
        if dominant_feature not in ["has_castling", "has_en_passant"]:
            order_by = f"""ORDER BY DESC(IF(?next_player = "white", ?white_{dominant_feature}, ?black_{dominant_feature}))\n"""
        else:
            order_by = ""
        print(f"Most dominant feature: {dominant_feature}")

        # Query to find similar puzzles based on dominant feature
        candidate_query = f"""
        PREFIX chess: <http://imaginealpacas.org/chess/>
        SELECT ?image ?puzzle_id ?next_player
               ?white_kings ?white_queens ?white_rooks ?white_bishops ?white_knights ?white_pawns
               ?black_kings ?black_queens ?black_rooks ?black_bishops ?black_knights ?black_pawns
        WHERE {{
            ?image chess:puzzle_id ?puzzle_id .
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

            FILTER (?puzzle_id NOT IN ({puzzle_id_conditions}))

            FILTER (
                # If castling is dominant
                ("{dominant_feature}" = "has_castling" && (
                    (?next_player = "white" && (BOUND(?white_castling_kingside) || BOUND(?white_castling_queenside))) ||
                    (?next_player = "black" && (BOUND(?black_castling_kingside) || BOUND(?black_castling_queenside)))
                ))
                ||
                # If en passant is dominant
                ("{dominant_feature}" = "has_en_passant" && (
                    (?next_player = "white" && BOUND(?en_passant_white)) ||
                    (?next_player = "black" && BOUND(?en_passant_black))
                ))
                ||
                # If a piece is dominant
                (?next_player = "white" && (BOUND(?white_{dominant_feature})))
                ||
                (?next_player = "black" && (BOUND(?black_{dominant_feature})))
            )
        }}
        {order_by}
        LIMIT 3
        """

        # Fetch candidate puzzles
        candidate_results = query_graphdb(candidate_query)

        recommendations = []
        for binding in candidate_results["results"]["bindings"]:
            recommendations.append({
                "puzzle_id": binding["puzzle_id"]["value"],
                "filename": extract_filename(binding["image"]["value"]),
                "next_player": binding["next_player"]["value"],
                "has_castling": int(binding.get("has_castling", {}).get("value", 0)),
                "has_en_passant": int(binding.get("has_en_passant", {}).get("value", 0)),
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
            })

        x = [recommendation["puzzle_id"] for recommendation in recommendations]
        print(x)

        return jsonify(recommendations)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
