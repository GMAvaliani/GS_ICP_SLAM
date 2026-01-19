import runpod
import subprocess
import os

def handler(event):
    data = event.get("input", {})
    dataset_path = data.get("dataset_path", "/workspace/dataset")

    # TODO: download dataset to dataset_path
    # Example: use wget/curl or Supabase SDK

    cmd = ["python", "gs_icp_slam.py", "--dataset_path", dataset_path]
    subprocess.run(cmd, check=True)

    return {"status": "done"}

runpod.serverless.start({"handler": handler})
