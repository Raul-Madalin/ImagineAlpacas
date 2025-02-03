from flask import Blueprint, request, jsonify
from config import BASE_URL
from utils.graphdb_utils import query_graphdb, extract_filename
import os
import cv2
import joblib
import numpy as np

# === Paths ===
path = os.path.dirname(os.path.dirname(__file__))
path = os.path.dirname(path)
TEST_DIR = os.path.join(path, "dataset", "test")
MODEL_PATH = os.path.join(path, "app", "recommender", "knn_model.pkl")

knn, train_image_paths = joblib.load(MODEL_PATH)

# === Feature Extraction Function ===
def extract_features(image_path):
    """Extract color histogram features from an image."""
    image = cv2.imread(image_path)
    image = cv2.resize(image, (128, 128))  # Resize for consistency
    hist = cv2.calcHist([image], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    hist = cv2.normalize(hist, hist).flatten()
    return hist

recommendation_ml_blueprint = Blueprint("recommendation-ml", __name__)

@recommendation_ml_blueprint.route("/ml-recommendations", methods=["POST"])
def get_recommendations():
    data = request.get_json()
    if not data or "puzzle_ids" not in data:
        return jsonify({"error": "Missing 'puzzle_ids' in request payload"}), 400

    puzzle_ids = data["puzzle_ids"]
    if not isinstance(puzzle_ids, list) or not puzzle_ids:
        return jsonify({"error": "'puzzle_ids' must be a non-empty list"}), 400

    try:
        # Construct a comma-separated string of puzzle ids for the SPARQL query.
        # (Assumes puzzle ids are numeric; if they are strings, add quotes accordingly.)
        puzzle_id_conditions = ", ".join(str(pid) for pid in puzzle_ids)

        # SPARQL query to fetch the image URIs (the subject in our RDF triples) for the given puzzle ids.
        sparql_query = f"""
        PREFIX chess: <http://imaginealpacas.org/chess/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT ?image ?puzzle_id
        WHERE {{
            ?image chess:puzzle_id ?puzzle_id .
            FILTER (?puzzle_id IN ({puzzle_id_conditions}))
        }}
        """

        # Query the RDF store
        results = query_graphdb(sparql_query)

        if "results" not in results or not results["results"]["bindings"]:
            return jsonify({"error": "No image information found for provided puzzle IDs"}), 404

        # Extract filenames from the returned image URIs
        filenames = []
        for binding in results["results"]["bindings"]:
            image_uri = binding["image"]["value"]
            filename = extract_filename(image_uri)
            filenames.append(filename)

        if not filenames:
            return jsonify({"error": "No filenames extracted from RDF results"}), 404

        # For each filename, build the full path and extract image features
        feature_list = []
        for fname in filenames:
            image_path = os.path.join(TEST_DIR, fname)
            if not os.path.exists(image_path):
                # You might choose to log this instead of returning an error immediately
                return jsonify({"error": f"Image file '{fname}' not found in '{TEST_DIR}'"}), 404
            features = extract_features(image_path)
            feature_list.append(features)

        # Compute the average feature vector from all displayed puzzles
        avg_features = np.mean(np.array(feature_list), axis=0).reshape(1, -1)

        # Use the k-NN model to find the index of the most similar image in the training set
        distances, indices = knn.kneighbors(avg_features)
        recommended_img_path = train_image_paths[indices[0][0]]
        recommended_filename = os.path.basename(recommended_img_path)

        print(f"Recommended Image: {recommended_filename}")

        # Return the recommended filename
        response = {
            "dominant_feature": "Unknown",
            "metadata": {
                "@context": "http://schema.org/",
                "@type": "ImageObject",
                "contentUrl": f"{BASE_URL}/images/{recommended_filename}",
                "encodingFormat": "image/png",
                "identifier": "Unknown",
                "name": f"Chess Puzzle Unknown",
                "recommendedFeature": "Unknown"
            }
        }
        
        return jsonify([response]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500