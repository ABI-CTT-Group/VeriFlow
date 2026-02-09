#!/usr/bin/env cwl-runner
cwlVersion: v1.2
class: CommandLineTool

label: DICOM to NIfTI Converter
doc: Converts DICOM images in a directory to NIfTI format using dicom2nifti

requirements:
  DockerRequirement:
    dockerPull: clin864/create-nifiti:latest
  InitialWorkDirRequirement:
    listing:
      - entry: $(inputs.dicom_images)
        writable: false

# The Docker image has ENTRYPOINT set to "python create_nifti.py"
# We just need to pass the arguments
baseCommand: []

inputs:
  dicom_images:
    type: Directory
    inputBinding:
      prefix: --input_folder
    doc: Directory containing DICOM image files

  output_folder:
    type: string
    default: "."
    inputBinding:
      prefix: --output_folder
    doc: Output folder path (uses CWL working directory)

outputs:
  nifti_images:
    type: File[]
    outputBinding:
      glob: "*.nii.gz"
    doc: The converted NIfTI image files
