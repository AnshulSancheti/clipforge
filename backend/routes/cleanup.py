from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Job, StorageObject

router = APIRouter()


@router.delete("/cleanup")
def cleanup_database(db: Session = Depends(get_db)):
    """Delete all jobs and storage objects from the database."""
    try:
        deleted_objects = db.query(StorageObject).delete()
        deleted_jobs = db.query(Job).delete()
        db.commit()
        return {
            "message": "Database cleaned successfully",
            "deleted_jobs": deleted_jobs,
            "deleted_storage_objects": deleted_objects,
        }
    except Exception as e:
        db.rollback()
        raise
