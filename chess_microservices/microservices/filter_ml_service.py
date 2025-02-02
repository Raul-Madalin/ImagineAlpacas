from flask import request, jsonify, Blueprint
import requests
from tensorflow.keras.models import load_model
import numpy as np
import cv2
import os
from utils.graphdb_utils import query_graphdb, extract_filename
import tensorflow as tf
from config import BASE_URL

filter_ml_blueprint = Blueprint("filter_game_state_ml", __name__)

temp_path = os.path.dirname(os.path.dirname(__file__))
temp_path = os.path.dirname(temp_path)
temp_path = f"{temp_path}\\app\\model\\chess_phase_model.h5"
print(temp_path)
model = load_model(temp_path)

# Preprocess image function
def preprocess_image(image_path):
    IMG_SIZE = 128

    # Load the image
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert from BGR to RGB
    image = cv2.resize(image, (IMG_SIZE, IMG_SIZE))  # Resize to 128x128

    # Normalize the image
    image = image.astype(np.float32) / 255.0

    # Add batch dimension
    image = np.expand_dims(image, axis=0)

    return image

# Predict game state using the model
def predict_game_state(image_path):
    image = preprocess_image(image_path)
    predictions = model.predict(image)

    phase_labels = {0: "opening", 1: "midgame", 2: "endgame"}
    predicted_index = np.argmax(predictions[0])
    return phase_labels[predicted_index]

@filter_ml_blueprint.route("/game-state-ml", methods=["POST"])
def filter_game_state_ml():
    """
    1. Retrieve candidate puzzles using SPARQL.
    2. Pass each candidate image to the ML model.
    3. If the prediction matches one of the game_states, return the puzzle.
    """
    data = request.json
    puzzle_ids = data.get("puzzle_ids", [])
    game_states = data.get("game_state", [])  # Example: ["opening", "midgame", "endgame"]

    if not puzzle_ids:
        return jsonify({"error": "No puzzle_ids provided for ML-based filtering"}), 400

    # --------------- 1) Retrieve Candidates with SPARQL ---------------
    sparql_query = """
    PREFIX chess: <http://imaginealpacas.org/chess/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT 
      ?image ?puzzle_id ?next_player
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
    puzzle_id_list = ", ".join(map(str, puzzle_ids))
    sparql_query += f"\nFILTER (?puzzle_id IN ({puzzle_id_list}))"
    sparql_query += "\n}"
    # sparql_query += "\n}LIMIT 100"

    try:
        sparql_results = query_graphdb(sparql_query)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    candidates = []
    for binding in sparql_results["results"]["bindings"]:
        candidates.append({
                "filename": extract_filename(binding["image"]["value"]),
                "puzzle_id": binding.get("puzzle_id", {}).get("value", ""),
                "next_player": binding.get("next_player", {}).get("value", ""),
                "game_state": binding.get("computed_state", {}).get("value", "unknown"),
                "metadata": {  # RDF-Compatible metadata
                  "@context": "http://schema.org/",
                  "@type": "ImageObject",
                  "identifier": binding.get("puzzle_id", {}).get("value", ""),
                  "name": f"Chess Puzzle {binding.get("puzzle_id", {}).get("value", "")}",
                  "contentUrl": f"{BASE_URL}/images/{extract_filename(binding["image"]["value"])}",
                  "encodingFormat": "image/png",
                }
            })

    print(f"Found {len(candidates)} candidates for ML-based filtering")
    # --------------- 2) Pass Images to ML Model ---------------
    filtered_puzzles = []
    for candidate in candidates:
        try:
            temp_path = os.path.dirname(os.path.dirname(__file__))
            temp_path = os.path.dirname(temp_path)
            image_path = f"{temp_path}/dataset/test/{candidate["filename"]}"
            # response = requests.get(image_path, stream=True)
            # if not os.path.exists(image_path):
            #     print(f"Image not found: {image_path}")
            #     continue

            predicted_phase = predict_game_state(image_path)
            if predicted_phase in game_states:
                candidate["game_state"] = predicted_phase
                filtered_puzzles.append(candidate)
        except Exception as e:
            print(f"Error processing image {candidate['filename']}: {e}")

    return jsonify(filtered_puzzles)