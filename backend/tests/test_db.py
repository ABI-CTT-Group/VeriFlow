import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestDatabaseConnection:
    """Tests for database connection."""
    
    @pytest.mark.asyncio
    async def test_get_db_yields_session(self):
        """Test that get_db yields a session."""
        from app.database import get_db
        
        # Mock the async session maker
        mock_session = AsyncMock()
        
        with patch('app.database.async_session_maker') as mock_maker:
            mock_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_maker.return_value.__aexit__ = AsyncMock(return_value=None)
            
            async for session in get_db():
                assert session == mock_session
    
    def test_base_class_exists(self):
        """Test that Base class is properly defined."""
        from app.database import Base
        
        assert Base is not None
        assert hasattr(Base, 'metadata')


class TestMinIOClient:
    """Tests for MinIO storage client."""
    
    def test_minio_client_initialization(self):
        """Test MinIO client can be initialized."""
        with patch('app.storage.Minio') as mock_minio:
            from app.storage import MinIOClient
            
            client = MinIOClient()
            assert client is not None
            assert client.bucket == "veriflow"
    
    def test_ensure_bucket_creates_if_not_exists(self):
        """Test ensure_bucket creates bucket if it doesn't exist."""
        with patch('app.storage.Minio') as mock_minio:
            mock_client = MagicMock()
            mock_client.bucket_exists.return_value = False
            mock_minio.return_value = mock_client
            
            from app.storage import MinIOClient
            client = MinIOClient()
            result = client.ensure_bucket()
            
            assert result is True
            mock_client.make_bucket.assert_called_once()
    
    def test_upload_file_success(self):
        """Test successful file upload."""
        with patch('app.storage.Minio') as mock_minio:
            mock_client = MagicMock()
            mock_client.bucket_exists.return_value = True
            mock_minio.return_value = mock_client
            
            from app.storage import MinIOClient
            client = MinIOClient()
            result = client.upload_file("test.pdf", b"test content", "application/pdf")
            
            assert result is True
            mock_client.put_object.assert_called_once()
    
    def test_file_exists_returns_true(self):
        """Test file_exists returns true for existing file."""
        with patch('app.storage.Minio') as mock_minio:
            mock_client = MagicMock()
            mock_minio.return_value = mock_client
            
            from app.storage import MinIOClient
            client = MinIOClient()
            result = client.file_exists("test.pdf")
            
            assert result is True


class TestConfig:
    """Tests for configuration."""
    
    def test_settings_defaults(self):
        """Test that settings have sensible defaults."""
        with patch.dict('os.environ', {}, clear=True):
            from app.config import Settings
            settings = Settings()
            
            assert "postgresql" in settings.database_url
            assert settings.minio_endpoint is not None
            assert settings.gemini_model == "gemini-2.0-flash"
