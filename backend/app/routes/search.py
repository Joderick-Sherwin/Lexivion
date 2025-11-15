from flask import Blueprint, jsonify, request

from ..services.search import search_rag_with_images


bp = Blueprint("search", __name__)


@bp.route("/search", methods=["POST"])
def search():
    try:
        data = request.get_json() or {}
        query = data.get("query", "").strip()
        top_k = int(data.get("top_k", 5))

        if not query:
            return jsonify({"error": "Query cannot be empty"}), 400

        if top_k < 1 or top_k > 50:
            return jsonify({"error": "top_k must be between 1 and 50"}), 400

        response_payload = search_rag_with_images(query, top_k)
        response_payload.update(
            {
                "query": query,
                "top_k": top_k,
            }
        )
        return jsonify(response_payload), 200
    
    except ValueError as e:
        return jsonify({"error": f"Invalid parameter: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Search failed: {str(e)}"}), 500

