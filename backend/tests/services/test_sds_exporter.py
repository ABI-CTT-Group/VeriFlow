import pytest
import json
import zipfile
import io
from app.services.export import SDSExporter


class TestSDSExporter:

    @pytest.fixture
    def exporter(self):
        return SDSExporter()

    @pytest.fixture
    def sample_inputs(self):
        return [{"id": "input1", "path": "data/input.nii.gz", "format": "application/x-nifti"}]

    @pytest.fixture
    def sample_outputs(self):
        return [
            {"id": "output1", "path": "derivative/mask.nii.gz", "node_id": "segmentation", "format": "application/x-nifti"},
        ]

    @pytest.fixture
    def sample_node_statuses(self):
        return {
            "segmentation": {"status": "completed", "started_at": "2026-01-01T00:00:00", "ended_at": "2026-01-01T00:05:00"},
        }

    def test_generate_dataset_description(self, exporter):
        """Test dataset_description.json generation."""
        desc = exporter.generate_dataset_description(
            execution_id="exec_123",
            workflow_id="wf_456",
            title="Test Results",
            description="Test description",
        )

        assert desc["name"] == "Test Results"
        assert desc["identifier"] == "exec_123"
        assert desc["version"] == "1.0.0"
        assert desc["license"] == "CC-BY-4.0"
        assert desc["sources"][0]["identifier"] == "wf_456"

    def test_generate_provenance_structure(self, exporter, sample_inputs, sample_outputs, sample_node_statuses):
        """Test provenance.json has correct structure."""
        prov = exporter.generate_provenance(
            execution_id="exec_123",
            workflow_id="wf_456",
            inputs=sample_inputs,
            outputs=sample_outputs,
            node_statuses=sample_node_statuses,
        )

        assert prov["execution_id"] == "exec_123"
        assert prov["workflow_id"] == "wf_456"
        assert "provenance" in prov
        assert "entities" in prov["provenance"]
        assert "activities" in prov["provenance"]
        assert "derivations" in prov["provenance"]

    def test_generate_provenance_derivation_links(self, exporter, sample_inputs, sample_outputs, sample_node_statuses):
        """Test wasDerivedFrom links are created between inputs and outputs."""
        prov = exporter.generate_provenance(
            execution_id="exec_123",
            workflow_id="wf_456",
            inputs=sample_inputs,
            outputs=sample_outputs,
            node_statuses=sample_node_statuses,
        )

        derivations = prov["provenance"]["derivations"]
        assert len(derivations) >= 1
        assert derivations[0]["generatedEntity"] == "output1"
        assert derivations[0]["activity"] == "segmentation"

    def test_generate_manifest_csv(self, exporter):
        """Test CSV manifest generation."""
        files = [
            {"filename": "output.nii.gz", "description": "Segmentation mask", "file_type": "nifti"},
        ]
        csv = exporter.generate_manifest_csv(files)

        assert "filename,timestamp,description,file type,additional type" in csv
        assert "output.nii.gz" in csv
        assert "Segmentation mask" in csv

    def test_generate_manifest_xlsx(self, exporter):
        """Test XLSX manifest generation (or empty bytes if openpyxl unavailable)."""
        files = [{"filename": "output.nii.gz", "description": "Mask"}]
        result = exporter.generate_manifest_xlsx(files)

        # Either valid xlsx bytes or empty bytes
        assert isinstance(result, bytes)

    def test_create_export_zip_structure(self, exporter, sample_inputs, sample_outputs, sample_node_statuses):
        """Test ZIP file contains expected files."""
        zip_bytes = exporter.create_export_zip(
            execution_id="exec_123",
            workflow_id="wf_456",
            title="Test",
            description="Test desc",
            inputs=sample_inputs,
            outputs=sample_outputs,
            node_statuses=sample_node_statuses,
            output_file_data={"mask.nii.gz": b"fake nifti data"},
        )

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert "dataset_description.json" in names
            assert "provenance.json" in names
            # manifest.xlsx or manifest.csv
            assert any(n.startswith("manifest") for n in names)

    def test_create_export_zip_contents(self, exporter, sample_inputs, sample_outputs, sample_node_statuses):
        """Test dataset_description.json inside ZIP has correct content."""
        zip_bytes = exporter.create_export_zip(
            execution_id="exec_123",
            workflow_id="wf_456",
            title="My Title",
            description="My desc",
            inputs=sample_inputs,
            outputs=sample_outputs,
            node_statuses=sample_node_statuses,
            output_file_data={},
        )

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            desc = json.loads(zf.read("dataset_description.json"))
            assert desc["name"] == "My Title"
            assert desc["identifier"] == "exec_123"

    def test_create_export_zip_output_files(self, exporter, sample_inputs, sample_outputs, sample_node_statuses):
        """Test output files are placed in derivative/ folder."""
        zip_bytes = exporter.create_export_zip(
            execution_id="exec_123",
            workflow_id="wf_456",
            title="Test",
            description="Test",
            inputs=sample_inputs,
            outputs=sample_outputs,
            node_statuses=sample_node_statuses,
            output_file_data={"result.txt": b"hello"},
        )

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert "derivative/exec_123/result.txt" in names
            assert zf.read("derivative/exec_123/result.txt") == b"hello"
