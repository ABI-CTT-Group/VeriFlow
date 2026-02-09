#!/usr/bin/env python
import argparse
import os
import subprocess
import sys

def run_nnunet_inference(input_folder, output_folder, dataset_name, configuration, folds, disable_tta, device):
    """Run nnUNet inference with the given parameters."""
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"📁 Created output directory: {output_folder}")

    # Start building the command
    command = [
        "nnUNetv2_predict",
        "-i", input_folder,
        "-o", output_folder,
        "-d", dataset_name,
        "-c", configuration,
        "-device", device,
        "-npp", "1", "-nps", "1" # Added these for CPU stability
    ]

    # Add folds if provided (handles multiple values like 0 1 2)
    if folds:
        command.extend(["-f"] + folds)

    # Add TTA disable flag if requested
    if disable_tta:
        command.append("--disable_tta")

    print(f"🚀 Running command: {' '.join(command)}")
    subprocess.run(command, check=True)

def main():
    parser = argparse.ArgumentParser(description="Run nnUNet inference on a dataset.")
    
    parser.add_argument("-i", "--input-folder", type=str, required=True)
    parser.add_argument("-o", "--output-folder", type=str, required=True)
    parser.add_argument("-d", "--dataset-name", type=str, default="1")
    parser.add_argument("-c", "--configuration", type=str, default="3d_fullres")
    
    # NEW ARGUMENTS
    parser.add_argument("-f", "--folds", nargs="+", help="Folds to use (e.g., 0 1 2)")
    parser.add_argument("--disable_tta", action="store_true", help="Disable test-time augmentation")
    parser.add_argument("-device", type=str, default="cpu", help="Device to use (cpu, cuda, mps)")
    
    parser.add_argument("--pre-trained-network", type=str, required=True)

    args = parser.parse_args()

    if args.pre_trained_network:
        os.environ['nnUNet_results'] = args.pre_trained_network

    run_nnunet_inference(
        args.input_folder, args.output_folder, args.dataset_name, 
        args.configuration, args.folds, args.disable_tta, args.device
    )

if __name__ == "__main__":
    main()