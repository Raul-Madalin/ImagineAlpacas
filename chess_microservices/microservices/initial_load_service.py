from flask import jsonify, Blueprint
from config import BASE_URL
from utils.graphdb_utils import query_graphdb, extract_filename

initial_load_blueprint = Blueprint("initial", __name__)

@initial_load_blueprint.route("/initial", methods=["GET"])
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
                "metadata": {  # RDF-Compatible metadata
                    "@context": "http://schema.org/",
                    "@type": "ImageObject",
                    "identifier": binding.get("puzzle_id", {}).get("value", "N/A"),
                    "name": f"Initial Chess Puzzle {binding.get("puzzle_id", {}).get("value", "N/A")}",
                    "contentUrl": f"{BASE_URL}/images/{extract_filename(binding["image"]["value"])}",
                    "encodingFormat": "image/png"
                }
            })

        return jsonify(chess_puzzles)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    