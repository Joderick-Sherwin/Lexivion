import os
from flask import Blueprint, current_app, jsonify, request

from ..services.pdf_processing import process_pdf


bp = Blueprint("ingest", __name__)


@bp.route("/upload", methods=["POST"])
def upload_pdf():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400
        
        if not file.filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files are allowed"}), 400

        target_dir = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(target_dir, exist_ok=True)
        
        # Sanitize filename
        safe_filename = os.path.basename(file.filename)
        file_path = os.path.join(target_dir, safe_filename)
        
        file.save(file_path)

        # Process PDF and capture ingestion stats
        ingestion_result = process_pdf(file_path, safe_filename)
        
        return jsonify({
            "message": f"{safe_filename} processed successfully!",
            "filename": safe_filename,
            "document_id": ingestion_result["document_id"],
            "chunks_stored": ingestion_result["text_chunks"],
            "images_stored": ingestion_result["image_chunks"],
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Failed to process PDF: {str(e)}"}), 500

