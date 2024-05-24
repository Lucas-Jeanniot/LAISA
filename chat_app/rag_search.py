import requests, json

def rag_search(self, user_message):
    """Perform a RAG search with the model."""
    if not self.database_name:
        self.add_message("Error: No database name provided.", "System")
        return

    url = f"http://localhost:9200/{self.database_name}/_search"
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
            for hit in hits:
                text = hit["_source"].get("text", "No text found.")
                # Send the retrieved document to the model for context inference
                self.send_document_to_model(user_message, text)
        else:
            self.add_message("No results found.", "System")
    except requests.exceptions.RequestException as e:
        self.add_message(f"Error: Unable to contact the database. {str(e)}", "System")
    except Exception as e:
        self.add_message(f"Error: {str(e)}", "System")
