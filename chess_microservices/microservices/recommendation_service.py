from flask import Blueprint, request, jsonify
from utils.graphdb_utils import query_graphdb, extract_filename

recommendation_blueprint = Blueprint("recommendation", __name__)

@recommendation_blueprint.route("/rdf-recommendations", methods=["POST"])
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
                "metadata": {  # RDF-Compatible metadata
                    "@context": "http://schema.org/",
                    "@type": "ImageObject",
                    "identifier": binding["puzzle_id"]["value"],
                    "name": f"Chess Puzzle {binding["puzzle_id"]["value"]}",
                    "contentUrl": f"http://localhost:5000/images/{extract_filename(binding["image"]["value"])}",
                    "encodingFormat": "image/png",
                    "recommendedFeature": f"{binding["next_player"]["value"]}"
                },
                "dominant_feature": dominant_feature
            })

        x = [recommendation["puzzle_id"] for recommendation in recommendations]
        print(x)

        return jsonify(recommendations)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
