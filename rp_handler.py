import runpod
import subprocess
import base64
import json
import os
from io import BytesIO
from PIL import Image
import requests

# Define paths
COMFYUI_API_URL = "http://localhost:8188/prompt"
WORKFLOW_PATH = "/ComfyUI/workflows/Inpainting-Basic.json"

def encode_image(image_path):
    """ Encode image as base64 string """
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

def decode_image(encoded_str, save_path):
    """ Decode base64 string and save as an image """
    img_data = base64.b64decode(encoded_str)
    img = Image.open(BytesIO(img_data))
    img.save(save_path)
    return save_path

def load_workflow():
    """ Load the ComfyUI workflow as a template """
    with open(WORKFLOW_PATH, "r") as file:
        return json.load(file)

def update_workflow(workflow, image_path, mask_path, prompt):
    """ Modify the workflow JSON with user inputs """
    for node in workflow["nodes"]:
        if node["type"] == "LoadImage":
            node["widgets_values"][0] = image_path
        elif node["type"] == "VAEEncodeForInpaint":
            node["inputs"]["pixels"] = image_path
            node["inputs"]["mask"] = mask_path
        elif node["type"] == "CLIPTextEncode":
            node["widgets_values"][0] = prompt
    return workflow

def process_batch(batch_inputs):
    """ Process batch inputs with ComfyUI """
    results = []
    
    for item in batch_inputs:
        prompt = item.get("prompt", "Default prompt")
        image_path = decode_image(item["image"], f"/tmp/input_{item['id']}.png")
        mask_path = decode_image(item["mask"], f"/tmp/mask_{item['id']}.png")
        
        # Load and modify workflow
        workflow = load_workflow()
        updated_workflow = update_workflow(workflow, image_path, mask_path, prompt)

        # Send request to ComfyUI
        response = requests.post(COMFYUI_API_URL, json=updated_workflow)
        
        if response.status_code == 200:
            output_path = f"/tmp/output_{item['id']}.png"
            result_image = response.json()["output"]  # Adjust according to ComfyUI's response format
            with open(output_path, "wb") as img_file:
                img_file.write(base64.b64decode(result_image))
            
            results.append({"id": item["id"], "output": encode_image(output_path)})
        else:
            results.append({"id": item["id"], "error": response.text})

    return results

def handler(event):
    """
    RunPod Serverless Handler
    Input: List of dicts with base64-encoded 'image', 'mask', and 'prompt'
    Output: List of dicts with base64-encoded 'output'
    """
    batch_inputs = event.get("input", [])
    if not batch_inputs:
        return {"error": "No valid input received"}
    
    return process_batch(batch_inputs)

if __name__ == '__main__':
    runpod.serverless.start({"handler": handler})
