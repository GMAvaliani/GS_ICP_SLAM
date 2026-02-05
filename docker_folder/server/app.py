from __future__ import annotations

import os
import subprocess
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    dataset_path: str = Field(..., description="Absolute or container path to dataset.")
    config_path: str = Field(..., description="Path to config file.")
    output_path: str = Field("experiments/results", description="Output directory.")
    extra_args: List[str] = Field(default_factory=list, description="Extra CLI args.")


class RunResponse(BaseModel):
    status: str
    command: List[str]
    output_path: str


app = FastAPI(title="GS-ICP SLAM API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse)
def run_slam(payload: RunRequest) -> RunResponse:
    repo_root = os.environ.get("GS_ICP_SLAM_ROOT", "/home/GS_ICP_SLAM")
    cmd = [
        "python",
        "-W",
        "ignore",
        "gs_icp_slam.py",
        "--dataset_path",
        payload.dataset_path,
        "--config",
        payload.config_path,
        "--output_path",
        payload.output_path,
        "--save_results",
        *payload.extra_args,
    ]
    try:
        subprocess.run(cmd, check=True, cwd=repo_root)
    except subprocess.CalledProcessError as exc:
        raise HTTPException(status_code=500, detail=f"SLAM failed: {exc}") from exc

    return RunResponse(status="completed", command=cmd, output_path=payload.output_path)
