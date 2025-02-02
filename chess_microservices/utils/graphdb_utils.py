import requests
import os
from urllib.parse import urlparse
from config import GRAPHDB_ENDPOINT

def query_graphdb(sparql_query):
    """
    Sends a SPARQL query to the GraphDB repository.
    """
    headers = {
        "Content-Type": "application/sparql-query",
        "Accept": "application/json",
    }
    response = requests.post(GRAPHDB_ENDPOINT, data=sparql_query, headers=headers)
    response.raise_for_status()
    return response.json()

def extract_filename(uri):
    return os.path.basename(urlparse(uri).path)
