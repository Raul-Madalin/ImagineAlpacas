from flask import Blueprint, request, jsonify
from config import BASE_URL
from utils.graphdb_utils import query_graphdb, extract_filename

search_blueprint = Blueprint("search", __name__)

@search_blueprint.route("/search", methods=["GET"])
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
                },
                "metadata": {  # RDF-Compatible metadata
                    "@context": "http://schema.org/",
                    "@type": "ImageObject",
                    "identifier": binding.get("puzzle_id", {}).get("value", "N/A"),
                    "name": f"Chess Puzzle {binding.get("puzzle_id", {}).get("value", "N/A")}",
                    "contentUrl": f"{BASE_URL}/images/{extract_filename(binding["image"]["value"])}",
                    "encodingFormat": "image/png",
                    "gameFeature": f"{binding.get("next_player", {}).get("value", "")} to move"
                }
            })

        return jsonify(chess_boards)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
