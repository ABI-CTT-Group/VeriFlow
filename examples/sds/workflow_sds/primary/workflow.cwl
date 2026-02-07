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



  pre_trained_network:
    type: Directory
    doc: Path to the pre-trained network (nnUNet_results) directory

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

      pre_trained_network: pre_trained_network
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
