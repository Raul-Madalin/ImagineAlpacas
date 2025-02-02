from flask import Blueprint, send_from_directory, abort, current_app
import os

image_blueprint = Blueprint("images", __name__)

@image_blueprint.route("/<filename>")
def serve_image(filename):
    path = os.path.dirname(current_app.root_path)
    if os.path.exists(f"{path}/dataset/test/{filename}"):
        return send_from_directory(f"{path}/dataset/test/", filename)
    elif os.path.exists(f"{path}/dataset/train/{filename}"):
        return send_from_directory(f"{path}/dataset/train/", filename)
    else:
        abort(404)
        