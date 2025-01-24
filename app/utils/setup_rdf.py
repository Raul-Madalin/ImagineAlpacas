import os
import rdflib

# Define RDF Namespace and Properties
def initialize_rdf():
    # Initialize RDF graph
    g = rdflib.Graph()

    # Define namespaces
    EX = rdflib.Namespace("http://example.org/chess/")
    RDF = rdflib.RDF

    # Bind namespace to prefixes
    g.bind("ex", EX)

    return g, EX


def castling_rights_to_natural(castling_rights: str) -> str:
    if castling_rights == "-":
        return "No castling available"
    parts = []
    if "K" in castling_rights:
        parts.append("White-Kingside")
    if "Q" in castling_rights:
        parts.append("White-Queenside")
    if "k" in castling_rights:
        parts.append("Black-Kingside")
    if "q" in castling_rights:
        parts.append("Black-Queenside")
    return ", ".join(parts)


def extract_properties_from_fen(fen):
    # Parse FEN representation for chess board metadata
    fen_parts = fen.split("-")  # Adjust to handle hyphen-separated FEN
    board = "".join(fen_parts[:8])  # First 8 parts represent the board

    castling_rights = fen_parts[8] if len(fen_parts) > 8 else "-"
    en_passant_target_square = fen_parts[9] if len(fen_parts) > 9 else "-"
    active_color = fen_parts[10] if len(fen_parts) > 10 else "-"
    fullmove_number = int(fen_parts[11]) if len(fen_parts) > 11 else 0

    properties = {
        "pawns": board.count("P") + board.count("p"),
        "bishops": board.count("B") + board.count("b"),
        "knights": board.count("N") + board.count("n"),
        "rooks": board.count("R") + board.count("r"),
        "queens": board.count("Q") + board.count("q"),
        "castling_rights": castling_rights_to_natural(castling_rights),
        "en_passant_target_square": en_passant_target_square,
        "active_color": "White" if active_color == "w" else "Black" if active_color == "b" else "-",
        "fullmove_number": fullmove_number,
    }

    return properties


def add_image_metadata_to_rdf(graph, namespace, image_name, properties):
    # Add metadata to RDF graph
    image_uri = namespace[image_name]

    for key, value in properties.items():
        graph.add((
            image_uri,
            namespace[key],
            rdflib.Literal(value)
        ))


# Example Use Case
def prepare_rdf_dataset(dataset_dir):
    g, EX = initialize_rdf()

    for file_name in os.listdir(dataset_dir):
        if file_name.endswith(".jpeg"):
            fen_representation = file_name.replace(".jpeg", "")
            properties = extract_properties_from_fen(fen_representation)
            add_image_metadata_to_rdf(g, EX, file_name, properties)
        break

    # Serialize to file
    path = os.path.dirname(os.path.dirname(__file__))
    path = os.path.dirname(path)
    g.serialize(os.path.join(path, 'ontology.rdf'), format="xml")


# Prepare RDF dataset
path = os.path.dirname(os.path.dirname(__file__))
path = os.path.dirname(path)
prepare_rdf_dataset(os.path.join(path, 'dataset', 'test'))
# prepare_rdf_dataset("./dataset/train")
