import requests, json, logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, filename='response_log.log', filemode='a', format='%(asctime)s - %(message)s')

def retrieve_document(database_name, user_message):
    """Retrieve document from OpenSearch."""
    url = f"http://localhost:9200/{database_name}/_search"
    payload = {
        "_source": {
            "excludes": ["passage_embedding"]
        },
        "query": {
            "neural": {
                "passage_embedding": {
                    "query_text": user_message,
                    "model_id": "y4L5WI8BlCBJfWriuN92",
                    "k": 1
                }
            }
        }
    }

    try:
        response = requests.get(url, params={"source": json.dumps(payload), "source_content_type": "application/json"})
        response.raise_for_status()
        results = response.json()
        hits = results.get("hits", {}).get("hits", [])
        if hits:
            source = hits[0]["_source"]
            document_text = source.get("text", "No text found.")
            return {"text": document_text}
        else:
            return {"text": "No results found."}
    except requests.exceptions.RequestException as e:
        logging.error(f"Error: Unable to contact the database. {str(e)}")
        return {"text": f"Error: Unable to contact the database. {str(e)}"}
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return {"text": f"Error: {str(e)}"}
