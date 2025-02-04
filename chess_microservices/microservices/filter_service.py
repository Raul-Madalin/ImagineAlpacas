from flask import request, jsonify, Blueprint
from config import BASE_URL
from utils.graphdb_utils import query_graphdb, extract_filename
import requests

filter_blueprint = Blueprint("filter", __name__)

@filter_blueprint.route("/filter", methods=["POST"])
def filter():
    """
    1) Piece-based filter.
    2) If 'game_state' in filters, internally call '/filter/game-state-rdf' 
       with the puzzle_ids returned from the piece filter.
    """
    data = request.json
    filters = data.get("filters", {})
    puzzle_ids = data.get("puzzle_ids", [])
    game_state_filter_endpoint = data.get("game_state_filter_endpoint", "")

    if not puzzle_ids:
        return jsonify({"error": "puzzle_ids are required"}), 400

    # Extract game_state if present, but do NOT remove it from 'filters' yet.
    # We'll remove it after piece filtering if we still need it.
    game_state_filters = filters.get("game_state")

    # --------------- 1) Do the piece-based filter ---------------
    # Build your piece-only SPARQL:
    sparql_query = """
    PREFIX chess: <http://imaginealpacas.org/chess/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
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

    # Limit puzzle_ids
    puzzle_id_list = ", ".join(map(str, puzzle_ids))
    sparql_query += f"\nFILTER (?puzzle_id IN ({puzzle_id_list})) "

    # Build piece conditions
    piece_conditions = []
    # We "pop" the game_state from 'filters' so it doesn't break piece logic:
    piece_filters = dict(filters)  # shallow copy
    piece_filters.pop("game_state", None)  # remove game_state if present

    for piece, values in piece_filters.items():
        if values:
            subconds = []
            for v in values:
                if v == "3+":
                    subconds.append(
                        f"((?next_player = \"white\" && ?white_{piece} >= 3) "
                        f"|| (?next_player = \"black\" && ?black_{piece} >= 3))"
                    )
                elif v == "2+":
                    subconds.append(
                        f"((?next_player = \"white\" && ?white_{piece} >= 2) "
                        f"|| (?next_player = \"black\" && ?black_{piece} >= 2))"
                    )
                elif v == "9+":
                    subconds.append(
                        f"((?next_player = \"white\" && ?white_{piece} >= 9) "
                        f"|| (?next_player = \"black\" && ?black_{piece} >= 9))"
                    )
                else:
                    # numeric
                    subconds.append(
                        f"((?next_player = \"white\" && ?white_{piece} = {v}) "
                        f"|| (?next_player = \"black\" && ?black_{piece} = {v}))"
                    )
            piece_conditions.append(f"FILTER ({' || '.join(subconds)})")

    if piece_conditions:
        sparql_query += "\n" + "\n".join(piece_conditions)

    sparql_query += "\n} ORDER BY ASC(xsd:integer(?puzzle_id))"

    # Run the piece-based filter
    try:
        piece_results = query_graphdb(sparql_query)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Parse those results
    piece_filtered_puzzles = []
    for index, binding in enumerate(piece_results["results"]["bindings"]):
        piece_filtered_puzzles.append({
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
            "metadata": {  # RDF-Compatible metadata
                "@context": "http://schema.org/",
                "@type": "ImageObject",
                "identifier": binding.get("puzzle_id", {}).get("value", "N/A"),
                "name": f"Chess Puzzle {binding.get("puzzle_id", {}).get("value", "N/A")}",
                "contentUrl": f"{BASE_URL}/images/{extract_filename(binding["image"]["value"])}",
                "encodingFormat": "image/png",
            }
        })

    # If the user did NOT request game_state filtering, just return these
    if not game_state_filters:
        return jsonify(piece_filtered_puzzles)

    # --------------- 2) If user wants game_state, call /filter/game-state-rdf ---------------
    # Gather puzzle_ids from the piece filter
    puzzle_ids_second = [p["puzzle_id"] for p in piece_filtered_puzzles if p["puzzle_id"] != "N/A"]
    # If no puzzles remain, we can return empty
    if not puzzle_ids_second:
        return jsonify([])

    # We'll call our second endpoint using requests
    second_payload = {
        "puzzle_ids": puzzle_ids_second,
        "game_state": game_state_filters
    }
    try:
        # Assume your Flask server is running locally; adjust host/port as needed
        second_resp = requests.post(game_state_filter_endpoint, json=second_payload)
        second_resp.raise_for_status()
        final_data = second_resp.json()
        return jsonify(final_data)
    except Exception as e:
        return jsonify({"error": f"Error calling /filter/game-state-rdf: {e}"}), 500
    