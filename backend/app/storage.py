from minio import Minio
from minio.error import S3Error
from app.config import get_settings
import io

settings = get_settings()


class MinIOClient:
    """MinIO object storage client."""
    
    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.bucket = settings.minio_bucket
    
    def ensure_bucket(self) -> bool:
        """Ensure the bucket exists, create if not."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
            return True
        except S3Error as e:
            print(f"MinIO error: {e}")
            return False
    
    def upload_file(self, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> bool:
        """Upload a file to MinIO."""
        try:
            self.ensure_bucket()
            self.client.put_object(
                self.bucket,
                object_name,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            return True
        except S3Error as e:
            print(f"Upload error: {e}")
            return False
    
    def download_file(self, object_name: str) -> bytes | None:
        """Download a file from MinIO."""
        try:
            response = self.client.get_object(self.bucket, object_name)
            return response.read()
        except S3Error as e:
            print(f"Download error: {e}")
            return None
        finally:
            response.close()
            response.release_conn()
    
    def file_exists(self, object_name: str) -> bool:
        """Check if a file exists in MinIO."""
        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except S3Error:
            return False


# Singleton instance
minio_client = MinIOClient()


def get_minio() -> MinIOClient:
    """Get MinIO client instance."""
    return minio_client
