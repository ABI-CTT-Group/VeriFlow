#!/usr/bin/env cwl-runner
cwlVersion: v1.2
class: CommandLineTool

label: nnUNet Inference
doc: Runs nnUNet inference on NIfTI images using a pre-trained model

requirements:
  DockerRequirement:
    dockerPull: clin864/run-inference:latest
  InitialWorkDirRequirement:
    listing:
      - entry: $(inputs.input_images)
        writable: false
      - entry: $(inputs.pre_trained_network)
        writable: false

baseCommand: ["python", "/app/run_inference.py"]

inputs:
  input_images:
    type: Directory
    inputBinding:
      prefix: --input-folder
    doc: Directory containing NIfTI images for inference

  output_folder:
    type: string
    default: "."
    inputBinding:
      prefix: --output-folder
    doc: Output folder path (uses CWL working directory)

  dataset_name:
    type: string
    default: "new_dataset"
    inputBinding:
      prefix: --dataset-name
    doc: nnUNet dataset name

  configuration:
    type: string
    default: "3d_fullres"
    inputBinding:
      prefix: --configuration
    doc: nnUNet configuration (e.g., 2d, 3d_fullres, 3d_lowres)

  pre_trained_network:
    type: Directory
    inputBinding:
      prefix: --pre-trained-network
    doc: Directory containing the pre-trained nnUNet model (nnUNet_results)

outputs:
  segmentation_results:
    type: File[]
    outputBinding:
      glob: "*.nii.gz"
    doc: Segmentation output files in NIfTI format
