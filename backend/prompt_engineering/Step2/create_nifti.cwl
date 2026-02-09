#!/usr/bin/env cwl-runner
cwlVersion: v1.2
class: CommandLineTool

label: DICOM to NIfTI Converter
doc: |
  Converts DICOM image series to NIfTI format using dicom2nifti.
  Loops through subfolders in the input directory and converts each to a NIfTI file.

baseCommand: ["python", "create_nifti.py"]

hints:
  SoftwareRequirement:
    packages:
      - package: dicom2nifti
        specs:
          - https://pypi.org/project/dicom2nifti/

requirements:
  DockerRequirement:
    dockerPull: python:3.9
    dockerImageId: dicom2nifti-tool
  NetworkAccess:
    networkAccess: true
  ShellCommandRequirement: {}
  InlineJavascriptRequirement: {}
  InitialWorkDirRequirement:
    listing:
      - entryname: create_nifti.py
        entry: |
          import os
          import dicom2nifti
          import argparse

          def convert_dicom_to_nifti(input_root, output_root):
              if not os.path.exists(output_root):
                  os.makedirs(output_root)
                  print(f"Created output folder: {output_root}")

              for item in os.listdir(input_root):
                  folder_path = os.path.join(input_root, item)
                  
                  if os.path.isdir(folder_path):
                      output_path = os.path.join(output_root, f"{item}_0000.nii.gz")
                      
                      try:
                          dicom2nifti.dicom_series_to_nifti(folder_path, output_path, reorient_nifti=True)
                      except Exception as e:
                          print(f"failed to convert {item}: {e}")

          if __name__ == "__main__":
              parser = argparse.ArgumentParser(description="convert nifti images")
              
              parser.add_argument(
                  "--input_folder", 
                  type=str, 
                  required=True, 
                  help="Path to the folder containing input images"
              )

              parser.add_argument(
                  "--output_folder", 
                  type=str, 
                  required=True, 
                  help="Path to the folder where converted NIfTI files will be saved"
              )
              args = parser.parse_args()
              
              convert_dicom_to_nifti(args.input_folder, args.output_folder)

inputs:
  input_folder:
    type: Directory
    inputBinding:
      prefix: --input_folder
    doc: Directory containing DICOM image subfolders to convert

  output_folder:
    type: string
    default: "nifti_output"
    inputBinding:
      prefix: --output_folder
    doc: Name of the output directory for converted NIfTI files

outputs:
  nifti_output:
    type: Directory
    outputBinding:
      glob: $(inputs.output_folder)
    doc: Directory containing the converted NIfTI files (.nii.gz)
