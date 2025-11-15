import os
from flask import Blueprint, abort, jsonify, send_file

from ..repository.rag_repository import fetch_document_by_id

bp = Blueprint("documents", __name__)


@bp.route("/documents/<int:doc_id>", methods=["GET"])
def get_document(doc_id: int):
    document = fetch_document_by_id(doc_id)
    if not document:
        abort(404, description="Document not found")
    return jsonify(
        {
            "id": document["id"],
            "filename": document["filename"],
            "metadata": document.get("metadata", {}),
        }
    )


@bp.route("/documents/<int:doc_id>/file", methods=["GET"])
def stream_document(doc_id: int):
    document = fetch_document_by_id(doc_id)
    if not document:
        abort(404, description="Document not found")

    source_path = document.get("source_path")
    if not source_path or not os.path.exists(source_path):
        abort(404, description="Document file missing on server")

    return send_file(
        source_path,
        mimetype="application/pdf",
        download_name=document["filename"],
        as_attachment=False,
    )

