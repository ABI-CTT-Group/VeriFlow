#!/usr/bin/env cwl-runner
cwlVersion: v1.2
class: CommandLineTool

label: nnUNet Inference
doc: |
  Runs nnUNet inference on a dataset to generate segmentation results.
  Wraps the nnUNetv2_predict command with configurable parameters.
  Uses PyTorch CUDA base image with nnUNetv2 installed at runtime.

baseCommand: ["bash", "-c"]

arguments:
  - valueFrom: |
      pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu && pip install nnunetv2 && python run_inference.py $(inputs.input_folder.path) $(inputs.output_folder) $(inputs.dataset_name) $(inputs.configuration) $(inputs.pre_trained_network.path)
    shellQuote: false

requirements:
  DockerRequirement:
    dockerPull: python:3.10-slim
  InitialWorkDirRequirement:
    listing:
      - entryname: run_inference.py
        entry: |
          #!/usr/bin/env python
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

              print(f"Running command: {' '.join(command)}")
              subprocess.run(command, check=True)

          def main():
              if len(sys.argv) != 6:
                  print("Usage: run_inference.py <input_folder> <output_folder> <dataset_name> <configuration> <pre_trained_network>")
                  sys.exit(1)

              input_folder = sys.argv[1]
              output_folder = sys.argv[2]
              dataset_name = sys.argv[3]
              configuration = sys.argv[4]
              pre_trained_network = sys.argv[5]

              # Set nnUNet_results environment variable
              os.environ['nnUNet_results'] = pre_trained_network
              print(f"Set nnUNet_results to: {pre_trained_network}")

              run_nnunet_inference(
                  input_folder=input_folder,
                  output_folder=output_folder,
                  dataset_name=dataset_name,
                  configuration=configuration
              )

          if __name__ == "__main__":
              main()

inputs:
  input_folder:
    type: Directory
    doc: Directory containing images for inference

  output_folder:
    type: string
    default: "inference_output"
    doc: Name of the output directory for segmentation results

  dataset_name:
    type: string?
    default: "new_dataset"
    doc: Name of the dataset

  configuration:
    type: string?
    default: "3d_fullres"
    doc: nnUNet configuration (e.g., 3d_fullres, 2d)

  pre_trained_network:
    type: Directory
    doc: Path to the pre-trained network (nnUNet_results) directory

outputs:
  segmentation_output:
    type: Directory
    outputBinding:
      glob: $(inputs.output_folder)
    doc: Directory containing the segmentation results
