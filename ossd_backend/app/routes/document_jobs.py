# app/routes/document_jobs.py

from flask import Blueprint, request, jsonify
from app import db
from app.models.document_job import DocumentJob, DocumentJobStatus
from flask_jwt_extended import jwt_required

bp = Blueprint("document_jobs", __name__, url_prefix="/api/v1/document_jobs")


@bp.route("/<int:job_id>", methods=["GET"])
@jwt_required()
def get_job_status(job_id):
    job = DocumentJob.query.get_or_404(job_id)
    return jsonify(code=200, data=job.to_dict())
