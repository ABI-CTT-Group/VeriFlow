# Use the full PyTorch image (avoids the 'libgl' issues of slim)
FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

WORKDIR /app

# Set the environment variables nnU-Net requires to function
ENV nnUNet_raw="/app/nnUNet_raw"
ENV nnUNet_preprocessed="/app/nnUNet_preprocessed"
ENV nnUNet_results="/app/nnUNet_results"

RUN mkdir /input
RUN mkdir /output

# copy dicom to /app/dicom
# cop nifti to /app/nnUNet_raw: DUKE_MRI_001_0000.nii.gz
# copy nnUNet_results to /app/nnUNet_results/Dataset001_DUKE: nnUNetTrainer__nnUNetPlans__3d_fullres
COPY ../examples/sds/measurement_sds_duke_mri/primary/sub-1 /app/dicom
COPY ../examples/sds/measurement_sds_nifti/primary/sub-1/sam-1 /app/nnUNet_raw
COPY ../examples/sds/model_sds_nnunet_pretrained_weights/primary /app/nnUNet_results/Dataset001_DUKE

# Install basic imaging dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# install dicom2nifti
RUN pip install --no-cache-dir dicom2nifti

# Install nnU-Net v2
RUN pip install --no-cache-dir nnunetv2
