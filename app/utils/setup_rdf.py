from collections import Counter
import os
import rdflib

# Define RDF Namespace and Properties
def initialize_rdf():
    # Initialize RDF graph
    g = rdflib.Graph()

    # Define namespaces
    CHESS = rdflib.Namespace("http://imaginealpacas.org/chess/")

    # Bind namespace to prefixes
    g.bind("chess", CHESS)

    return g, CHESS


def extract_properties_from_fen(fen):
    properties = {}

    rows = fen.split('-')
    board = []
    for row in rows:
        expanded_row = ""
        for char in row:
            if char.isdigit():
                expanded_row += '.' * int(char)  # Empty squares
            else:
                expanded_row += char
        board.append(expanded_row)

    # Determine which side is playing from the bottom
    bottom_pieces = Counter("".join(board[4:8]))
    bottom_white = sum(bottom_pieces[p] for p in "PNBRQK")
    bottom_black = sum(bottom_pieces[p] for p in "pnbrqk")
    if bottom_white > bottom_black:
        properties["next_player"] = "white"
    else:
        properties["next_player"] = "black"

    # Count individual pieces for each color
    piece_counter = Counter("".join(board))
    properties["white_pieces"] = {
        'kings': piece_counter.get('K', 0),
        'queens': piece_counter.get('Q', 0),
        'rooks': piece_counter.get('R', 0),
        'bishops': piece_counter.get('B', 0),
        'knights': piece_counter.get('N', 0),
        'pawns': piece_counter.get('P', 0),
    }
    properties["black_pieces"] = {
        'kings': piece_counter.get('k', 0),
        'queens': piece_counter.get('q', 0),
        'rooks': piece_counter.get('r', 0),
        'bishops': piece_counter.get('b', 0),
        'knights': piece_counter.get('n', 0),
        'pawns': piece_counter.get('p', 0),
    }

    # Determine castling rights
    properties["castling"] = {
        'white_castling_kingside': board[7][4] == 'K' and board[7][7] == 'R',  # e1 and h1
        'white_castling_queenside': board[7][4] == 'K' and board[7][0] == 'R',   # e1 and a1
        'black_castling_kingside': board[0][4] == 'k' and board[0][7] == 'r',  # e8 and h8
        'black_castling_queenside': board[0][4] == 'k' and board[0][0] == 'r'   # e8 and a8
    }

    properties["en_passant_white"] = False
    properties["en_passant_black"] = False
    if properties["next_player"] == "white":
        for j in range(8):  # Iterate over columns
            # Check White pawns on rank 5
            if board[4][j] == 'P':  # White pawn on rank 5
                if (j > 0 and board[4][j - 1] == 'p') or (j < 7 and board[4][j + 1] == 'p'):
                    properties["en_passant_white"] = True

            # Check Black pawns on rank 5
            if board[4][j] == 'p':  # Black pawn on rank 5
                if (j > 0 and board[4][j - 1] == 'P') or (j < 7 and board[4][j + 1] == 'P'):
                    properties["en_passant_black"] = True

    elif properties["next_player"] == "black":
        for j in range(8):  # Iterate over columns
            # Check White pawns on rank 4
            if board[3][j] == 'P':  # White pawn on rank 4
                if (j > 0 and board[3][j - 1] == 'p') or (j < 7 and board[3][j + 1] == 'p'):
                    properties["en_passant_white"] = True

            # Check Black pawns on rank 4
            if board[3][j] == 'p':  # Black pawn on rank 4
                if (j > 0 and board[3][j - 1] == 'P') or (j < 7 and board[3][j + 1] == 'P'):
                    properties["en_passant_black"] = True

    return properties


def add_image_metadata_to_rdf(graph, CHESS, image_name, properties):
    image_uri = CHESS[image_name]

    # # Add a comment to indicate the start of a new chess board
    # graph.add((image_uri, rdflib.RDFS.comment, rdflib.Literal(f"Chess board representation for {image_name}")))

    # Store the next player
    graph.add((image_uri, CHESS["next_player"], rdflib.Literal(properties["next_player"])))

    # Create a resource for white pieces
    white_pieces_uri = CHESS[f"{image_name}_WhitePieces"]
    graph.add((image_uri, CHESS["white_pieces"], white_pieces_uri))
    graph.add((white_pieces_uri, rdflib.RDF.type, CHESS["ChessPieceCollection"]))

    # Create a resource for black pieces
    black_pieces_uri = CHESS[f"{image_name}_BlackPieces"]
    graph.add((image_uri, CHESS["black_pieces"], black_pieces_uri))
    graph.add((black_pieces_uri, rdflib.RDF.type, CHESS["ChessPieceCollection"]))

    # Store piece counts inside white_pieces and black_pieces
    for piece, count in properties["white_pieces"].items():
        graph.add((white_pieces_uri, CHESS[f"white_pieces_{piece}"], rdflib.Literal(count)))

    for piece, count in properties["black_pieces"].items():
        graph.add((black_pieces_uri, CHESS[f"black_pieces_{piece}"], rdflib.Literal(count)))

    # Store castling rights
    for castling_right, status in properties["castling"].items():
        graph.add((image_uri, CHESS[castling_right], rdflib.Literal(status)))

    # Store en passant possibilities
    graph.add((image_uri, CHESS["en_passant_white"], rdflib.Literal(properties["en_passant_white"])))
    graph.add((image_uri, CHESS["en_passant_black"], rdflib.Literal(properties["en_passant_black"])))


# Example Use Case
def prepare_rdf_dataset(dataset_dir):
    g, CHESS = initialize_rdf()

    index = 0
    for file_name in os.listdir(dataset_dir):
        if file_name.endswith(".jpeg"):
            fen_representation = file_name.replace(".jpeg", "")
            properties = extract_properties_from_fen(fen_representation)
            add_image_metadata_to_rdf(g, CHESS, file_name, properties)
            index += 1
        if index == 10:
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
