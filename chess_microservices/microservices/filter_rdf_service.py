from flask import request, jsonify, Blueprint
from utils.graphdb_utils import query_graphdb, extract_filename

filter_rdf_blueprint = Blueprint("filter_game_state_rdf", __name__)

@filter_rdf_blueprint.route("/game-state-rdf", methods=["POST"])
def filter_game_state_rdf():
    """
    Expects puzzle_ids from the piece filter,
    plus an array game_state, e.g. ["opening","endgame"].
    Classifies each puzzle's total_pieces => opening/midgame/endgame,
    then filters accordingly.
    """
    data = request.json
    puzzle_ids = data.get("puzzle_ids", [])
    game_states = data.get("game_state", [])

    if not puzzle_ids:
        return jsonify({"error": "No puzzle_ids provided for game-state filtering"}), 400

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

      BIND(
        IF(
          ?total_pieces >= 24,
          "opening",
          IF(
            ?total_pieces >= 14,
            "midgame",
            "endgame"
          )
        ) AS ?computed_state
      )
    """

    puzzle_id_list = ", ".join(map(str, puzzle_ids))
    sparql_query += f"\nFILTER (?puzzle_id IN ({puzzle_id_list})) "

    if game_states:
        states_str = ", ".join(f"\"{s}\"" for s in game_states)
        sparql_query += f"\nFILTER(?computed_state IN ({states_str}))"

    sparql_query += "\n} ORDER BY ASC(xsd:integer(?puzzle_id))"

    try:
        results = query_graphdb(sparql_query)
        final_puzzles = []
        for index, binding in enumerate(results["results"]["bindings"]):
            final_puzzles.append({
                "index": index + 1,
                "filename": extract_filename(binding["image"]["value"]),
                "puzzle_id": binding.get("puzzle_id", {}).get("value", ""),
                "next_player": binding.get("next_player", {}).get("value", ""),
                "game_state": binding.get("computed_state", {}).get("value", "unknown"),
                "metadata": {  # RDF-Compatible metadata
                  "@context": "http://schema.org/",
                  "@type": "ImageObject",
                  "identifier": binding.get("puzzle_id", {}).get("value", ""),
                  "name": f"Chess Puzzle {binding.get("puzzle_id", {}).get("value", "")}",
                  "contentUrl": f"http://localhost:5000/images/{extract_filename(binding["image"]["value"])}",
                  "encodingFormat": "image/png",
                }
            })
        return jsonify(final_puzzles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    