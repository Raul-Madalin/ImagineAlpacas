from flask import Flask
from flask_cors import CORS
from microservices.search_service import search_blueprint
from microservices.filter_service import filter_blueprint
from microservices.recommendation_service import recommendation_blueprint
from microservices.image_service import image_blueprint
from microservices.initial_load_service import initial_load_blueprint
from microservices.filter_rdf_service import filter_rdf_blueprint

app = Flask(__name__)
CORS(app)

# Register Blueprints
app.register_blueprint(search_blueprint, url_prefix="/")
app.register_blueprint(filter_blueprint, url_prefix="/")
app.register_blueprint(filter_rdf_blueprint, url_prefix="/filter")
app.register_blueprint(recommendation_blueprint, url_prefix="/")
app.register_blueprint(image_blueprint, url_prefix="/images")
app.register_blueprint(initial_load_blueprint, url_prefix="/")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
