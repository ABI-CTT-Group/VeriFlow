#!/usr/bin/env python
import argparse
import os
import subprocess
import sys


def run_nnunet_inference(input_folder: str, output_folder: str, dataset_name: str, configuration: str):
    """Run nnUNet inference with the given parameters."""
    
    # Ensure the output directory exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"📁 Created output directory: {output_folder}")

    # Construct and run the command
    command = [
        "nnUNetv2_predict",
        "-i", input_folder,
        "-o", output_folder,
        "-d", dataset_name,
        "-c", configuration
    ]

    subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser(
        description="Run nnUNet inference on a dataset."
    )
    
    # Required arguments
    parser.add_argument(
        "-i", "--input-folder",
        type=str,
        required=True,
        help="Path to the input folder containing images for inference."
    )
    parser.add_argument(
        "-o", "--output-folder",
        type=str,
        required=True,
        help="Path to the output folder for segmentation results."
    )
    
    # Optional arguments with environment variable fallbacks
    parser.add_argument(
        "-d", "--dataset-name",
        type=str,
        default=os.environ.get("NNUNET_DATASET_NAME", "new_dataset"),
        help="Name of the dataset (default: env NNUNET_DATASET_NAME or 'new_dataset')."
    )
    parser.add_argument(
        "-c", "--configuration",
        type=str,
        default=os.environ.get("NNUNET_CONFIGURATION", "3d_fullres"),
        help="nnUNet configuration (default: env NNUNET_CONFIGURATION or '3d_fullres')."
    )
    
    # nnUNet environment paths (optional, can be set via env vars)
    parser.add_argument(
        "--nnunet-raw",
        type=str,
        default=os.environ.get("nnUNet_raw"),
        help="Path to nnUNet_raw directory (default: env nnUNet_raw)."
    )
    parser.add_argument(
        "--nnunet-preprocessed",
        type=str,
        default=os.environ.get("nnUNet_preprocessed"),
        help="Path to nnUNet_preprocessed directory (default: env nnUNet_preprocessed)."
    )
    parser.add_argument(
        "--nnunet-results",
        type=str,
        default=os.environ.get("nnUNet_results"),
        help="Path to nnUNet_results directory (default: env nnUNet_results)."
    )

    args = parser.parse_args()

    # Set nnUNet environment variables if provided via CLI
    if args.nnunet_raw:
        os.environ['nnUNet_raw'] = args.nnunet_raw
    if args.nnunet_preprocessed:
        os.environ['nnUNet_preprocessed'] = args.nnunet_preprocessed
    if args.nnunet_results:
        os.environ['nnUNet_results'] = args.nnunet_results

    run_nnunet_inference(
        input_folder=args.input_folder,
        output_folder=args.output_folder,
        dataset_name=args.dataset_name,
        configuration=args.configuration
    )


if __name__ == "__main__":
    main()
