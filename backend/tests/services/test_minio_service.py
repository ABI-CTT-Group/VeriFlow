import pytest
import sys
import io
from unittest.mock import MagicMock, patch, PropertyMock
from app.services.minio_client import MinIOService

# Create a real S3Error exception class since minio is globally mocked
class _S3Error(Exception):
    """Stand-in for minio.error.S3Error that can be caught by except clauses."""
    pass

# Patch the mock module's S3Error with our real exception class
# so that `from minio.error import S3Error` gives a catchable exception
sys.modules['minio.error'].S3Error = _S3Error
sys.modules['minio'].error = sys.modules['minio.error']


class TestMinIOService:

    @pytest.fixture
    def service(self):
        """Create MinIOService with mocked Minio client."""
        with patch("app.services.minio_client.Minio") as mock_cls, \
             patch("app.services.minio_client.S3Error", _S3Error):
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            svc = MinIOService()
            svc.client = mock_client
            yield svc

    def test_ensure_buckets_creates_missing(self, service):
        """Test ensure_buckets_exist creates missing buckets."""
        service.client.bucket_exists.return_value = False

        service.ensure_buckets_exist()

        assert service.client.make_bucket.call_count == 4  # 4 buckets

    def test_ensure_buckets_skips_existing(self, service):
        """Test ensure_buckets_exist skips existing buckets."""
        service.client.bucket_exists.return_value = True

        service.ensure_buckets_exist()

        service.client.make_bucket.assert_not_called()

    def test_upload_file(self, service):
        """Test upload_file calls put_object."""
        data = io.BytesIO(b"hello world")
        result = service.upload_file(
            bucket="measurements",
            object_name="test/file.pdf",
            file_data=data,
            content_type="application/pdf",
            length=11,
        )

        service.client.put_object.assert_called_once()
        assert result == "measurements/test/file.pdf"

    def test_download_file(self, service):
        """Test download_file reads from response."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"file content"
        service.client.get_object.return_value = mock_response

        result = service.download_file("measurements", "test/file.pdf")

        assert result == b"file content"
        mock_response.close.assert_called_once()
        mock_response.release_conn.assert_called_once()

    def test_get_presigned_download_url(self, service):
        """Test presigned URL generation."""
        service.client.presigned_get_object.return_value = "https://presigned-url"

        url = service.get_presigned_download_url("measurements", "test/file.pdf")

        assert url == "https://presigned-url"
        service.client.presigned_get_object.assert_called_once()

    def test_list_objects(self, service):
        """Test list_objects returns formatted list."""
        mock_obj = MagicMock()
        mock_obj.object_name = "test/file.pdf"
        mock_obj.size = 1024
        mock_obj.last_modified = None
        mock_obj.content_type = "application/pdf"
        service.client.list_objects.return_value = [mock_obj]

        result = service.list_objects("measurements", prefix="test/")

        assert len(result) == 1
        assert result[0]["name"] == "test/file.pdf"
        assert result[0]["size"] == 1024

    def test_delete_object_success(self, service):
        """Test successful object deletion."""
        result = service.delete_object("measurements", "test/file.pdf")

        assert result is True
        service.client.remove_object.assert_called_once_with("measurements", "test/file.pdf")

    def test_delete_object_failure(self, service):
        """Test object deletion failure returns False."""
        service.client.remove_object.side_effect = _S3Error("delete failed")

        result = service.delete_object("measurements", "nonexistent")

        assert result is False

    def test_object_exists_true(self, service):
        """Test object_exists returns True for existing objects."""
        service.client.stat_object.return_value = MagicMock()

        assert service.object_exists("measurements", "test/file.pdf") is True

    def test_object_exists_false(self, service):
        """Test object_exists returns False for missing objects."""
        service.client.stat_object.side_effect = _S3Error("not found")

        assert service.object_exists("measurements", "nonexistent") is False
