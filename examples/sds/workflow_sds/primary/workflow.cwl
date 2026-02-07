#!/usr/bin/env cwl-runner
cwlVersion: v1.2
class: Workflow

label: DICOM to Segmentation Pipeline
doc: |
  A workflow that converts DICOM images to NIfTI format and then runs
  nnUNet inference to generate segmentation results.

inputs:
  dicom_input:
    type: Directory
    doc: Directory containing DICOM image subfolders to process

  dataset_name:
    type: string?
    default: "new_dataset"
    doc: Name of the dataset for nnUNet inference

  configuration:
    type: string?
    default: "3d_fullres"
    doc: nnUNet configuration (e.g., 3d_fullres, 2d)

  nnunet_raw:
    type: Directory?
    doc: Path to nnUNet_raw directory

  nnunet_preprocessed:
    type: Directory?
    doc: Path to nnUNet_preprocessed directory

  nnunet_results:
    type: Directory?
    doc: Path to nnUNet_results directory

steps:
  create_nifti:
    run: create_nifti.cwl
    in:
      input_folder: dicom_input
    out: [nifti_output]

  run_inference:
    run: run_inference.cwl
    in:
      input_folder: create_nifti/nifti_output
      dataset_name: dataset_name
      configuration: configuration
      nnunet_raw: nnunet_raw
      nnunet_preprocessed: nnunet_preprocessed
      nnunet_results: nnunet_results
    out: [segmentation_output]

outputs:
  nifti_files:
    type: Directory
    outputSource: create_nifti/nifti_output
    doc: Directory containing the converted NIfTI files

  segmentation_results:
    type: Directory
    outputSource: run_inference/segmentation_output
    doc: Directory containing the segmentation results
