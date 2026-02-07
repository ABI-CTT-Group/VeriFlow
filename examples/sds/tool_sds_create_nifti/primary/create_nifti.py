import os
import dicom2nifti
import argparse

def convert_dicom_to_nifti(input_root, output_root):
    """
    Loops through the subfolders in input_root and converts each to a NIfTI file.
    """
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
        help="Path to the folder containing input images (e.g., imagesTs)"
    )

    parser.add_argument(
        "--output_folder", 
        type=str, 
        required=True, 
        help="Path to the folder where converted NIfTI files will be saved"
    )
    args = parser.parse_args()
    
    convert_dicom_to_nifti(args.input_folder, args.output_folder)