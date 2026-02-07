#!/usr/bin/env cwl-runner
cwlVersion: v1.2
class: CommandLineTool

label: nnUNet Inference
doc: |
  Runs nnUNet inference on a dataset to generate segmentation results.
  Wraps the nnUNetv2_predict command with configurable parameters.

baseCommand: ["python", "run_inference.py"]

requirements:
  DockerRequirement:
    dockerPull: python:3.9
  InitialWorkDirRequirement:
    listing:
      - entryname: run_inference.py
        entry: |
          #!/usr/bin/env python
          import argparse
          import os
          import subprocess
          import sys

          def run_nnunet_inference(input_folder: str, output_folder: str, dataset_name: str, configuration: str):
              if not os.path.exists(output_folder):
                  os.makedirs(output_folder)
                  print(f"Created output directory: {output_folder}")

              command = [
                  "nnUNetv2_predict",
                  "-i", input_folder,
                  "-o", output_folder,
                  "-d", dataset_name,
                  "-c", configuration
              ]

              subprocess.run(command, check=True)

          def main():
              parser = argparse.ArgumentParser(description="Run nnUNet inference on a dataset.")
              
              parser.add_argument("-i", "--input-folder", type=str, required=True,
                  help="Path to the input folder containing images for inference.")
              parser.add_argument("-o", "--output-folder", type=str, required=True,
                  help="Path to the output folder for segmentation results.")
              parser.add_argument("-d", "--dataset-name", type=str,
                  default=os.environ.get("NNUNET_DATASET_NAME", "new_dataset"),
                  help="Name of the dataset.")
              parser.add_argument("-c", "--configuration", type=str,
                  default=os.environ.get("NNUNET_CONFIGURATION", "3d_fullres"),
                  help="nnUNet configuration.")

              parser.add_argument("--pre-trained-network", type=str, required=True,
                  help="Path to the pre-trained network (nnUNet_results) directory.")

              args = parser.parse_args()


              if args.pre_trained_network:
                  os.environ['nnUNet_results'] = args.pre_trained_network

              run_nnunet_inference(
                  input_folder=args.input_folder,
                  output_folder=args.output_folder,
                  dataset_name=args.dataset_name,
                  configuration=args.configuration
              )

          if __name__ == "__main__":
              main()

inputs:
  input_folder:
    type: Directory
    inputBinding:
      prefix: --input-folder
    doc: Directory containing images for inference

  output_folder:
    type: string
    default: "inference_output"
    inputBinding:
      prefix: --output-folder
    doc: Name of the output directory for segmentation results

  dataset_name:
    type: string?
    default: "new_dataset"
    inputBinding:
      prefix: --dataset-name
    doc: Name of the dataset

  configuration:
    type: string?
    default: "3d_fullres"
    inputBinding:
      prefix: --configuration
    doc: nnUNet configuration (e.g., 3d_fullres, 2d)



  pre_trained_network:
    type: Directory
    inputBinding:
      prefix: --pre-trained-network
    doc: Path to the pre-trained network (nnUNet_results) directory

outputs:
  segmentation_output:
    type: Directory
    outputBinding:
      glob: $(inputs.output_folder)
    doc: Directory containing the segmentation results
