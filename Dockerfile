FROM python:3.12

# Clone the repository
RUN git clone https://github.com/comfyanonymous/ComfyUI.git

# Set the working directory
WORKDIR /ComfyUI

# Update pip, install GPU dependencies, and install ComfyUI dependencies
RUN pip install --upgrade pip
RUN pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu121
RUN pip install -r requirements.txt

# Install RunPod SDK
RUN pip install runpod

# Copy the serverless handler script into the container
COPY rp_handler.py /ComfyUI/

# Set the entry point for the container
CMD ["python3", "-u", "rp_handler.py"]
