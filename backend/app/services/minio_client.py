"""
VeriFlow - MinIO Service Layer
Handles object storage operations and presigned URL generation.
Per SPEC.md Section 8.2
"""

import os
from datetime import timedelta
from typing import Optional, List, BinaryIO
from minio import Minio
from minio.error import S3Error


class MinIOService:
    """Service layer for MinIO object storage operations."""
    
    # Bucket names per SPEC.md Section 8.1
    MEASUREMENTS_BUCKET = "measurements"
    WORKFLOW_BUCKET = "workflow"
    WORKFLOW_TOOL_BUCKET = "workflow-tool"
    PROCESS_BUCKET = "process"
    
    def __init__(self):
        """Initialize MinIO client from environment variables."""
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "veriflow")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "veriflow123")
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
        )
    
    def ensure_buckets_exist(self) -> None:
        """Create all required buckets if they don't exist."""
        buckets = [
            self.MEASUREMENTS_BUCKET,
            self.WORKFLOW_BUCKET,
            self.WORKFLOW_TOOL_BUCKET,
            self.PROCESS_BUCKET,
        ]
        for bucket in buckets:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
    
    def upload_file(
        self,
        bucket: str,
        object_name: str,
        file_data: BinaryIO,
        content_type: str = "application/octet-stream",
        length: int = -1,
    ) -> str:
        """
        Upload a file to MinIO.
        
        Returns the object path.
        """
        if length == -1:
            # Get file size
            file_data.seek(0, 2)
            length = file_data.tell()
            file_data.seek(0)
        
        self.client.put_object(
            bucket,
            object_name,
            file_data,
            length=length,
            content_type=content_type,
        )
        return f"{bucket}/{object_name}"
    
    def download_file(self, bucket: str, object_name: str) -> bytes:
        """Download a file from MinIO."""
        response = self.client.get_object(bucket, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()
    
    def get_presigned_download_url(
        self,
        bucket: str,
        object_name: str,
        expires: int = 3600,
    ) -> str:
        """
        Generate a presigned URL for file download.
        Per SPEC.md Section 8.2
        """
        return self.client.presigned_get_object(
            bucket,
            object_name,
            expires=timedelta(seconds=expires),
        )
    
    def get_presigned_upload_url(
        self,
        bucket: str,
        object_name: str,
        expires: int = 3600,
    ) -> str:
        """Generate a presigned URL for file upload."""
        return self.client.presigned_put_object(
            bucket,
            object_name,
            expires=timedelta(seconds=expires),
        )
    
    def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        recursive: bool = True,
    ) -> List[dict]:
        """List objects in a bucket with optional prefix filter."""
        objects = []
        for obj in self.client.list_objects(bucket, prefix=prefix, recursive=recursive):
            objects.append({
                "name": obj.object_name,
                "size": obj.size,
                "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                "content_type": obj.content_type,
            })
        return objects
    
    def delete_object(self, bucket: str, object_name: str) -> bool:
        """Delete an object from MinIO."""
        try:
            self.client.remove_object(bucket, object_name)
            return True
        except S3Error:
            return False
    
    def object_exists(self, bucket: str, object_name: str) -> bool:
        """Check if an object exists."""
        try:
            self.client.stat_object(bucket, object_name)
            return True
        except S3Error:
            return False


# Global service instance
minio_service = MinIOService()
