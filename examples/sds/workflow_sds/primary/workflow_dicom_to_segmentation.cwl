#!/usr/bin/env cwl-runner
cwlVersion: v1.2
class: Workflow

label: DICOM to Segmentation Pipeline
doc: |
  Complete pipeline that converts DICOM images to NIfTI format,
  then runs nnUNet inference to produce segmentation results.

requirements:
  SubworkflowFeatureRequirement: {}
  StepInputExpressionRequirement: {}
  InlineJavascriptRequirement: {}

inputs:
  dicom_images:
    type: Directory
    doc: Directory containing DICOM image files

  pre_trained_network:
    type: Directory
    doc: Directory containing the pre-trained nnUNet model (nnUNet_results)

  dataset_name:
    type: string
    default: "new_dataset"
    doc: nnUNet dataset name

  configuration:
    type: string
    default: "3d_fullres"
    doc: nnUNet configuration (e.g., 2d, 3d_fullres, 3d_lowres)

outputs:
  nifti_images:
    type: File[]
    outputSource: step1_create_nifti/nifti_images
    doc: Intermediate NIfTI images from DICOM conversion

  segmentation_results:
    type: File[]
    outputSource: step2_run_inference/segmentation_results
    doc: Final segmentation output files

steps:
  step1_create_nifti:
    run: create_nifti.cwl
    in:
      dicom_images: dicom_images
    out: [nifti_images]

  step2_run_inference:
    run: run_inference.cwl
    in:
      input_images:
        source: step1_create_nifti/nifti_images
        valueFrom: |
          ${
            return {
              "class": "Directory",
              "basename": "nifti_input",
              "listing": self
            };
          }
      pre_trained_network: pre_trained_network
      dataset_name: dataset_name
      configuration: configuration
    out: [segmentation_results]
