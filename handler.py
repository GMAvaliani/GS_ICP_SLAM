import os
import shlex
import subprocess
from typing import Any, Dict, List, Union

import runpod


def _normalize_command(command: Union[str, List[str]]) -> List[str]:
    if isinstance(command, str):
        return shlex.split(command)
    return command


def _build_command(input_data: Dict[str, Any]) -> List[str]:
    if "command" in input_data:
        return _normalize_command(input_data["command"])

    script = input_data.get("script", "gs_icp_slam.py")
    dataset_path = input_data.get(
        "dataset_path", os.environ.get("DATASET_PATH", "dataset/Replica/room0")
    )
    config = input_data.get(
        "config", os.environ.get("CONFIG_PATH", "configs/Replica/caminfo.txt")
    )
    output_path = input_data.get(
        "output_path", os.environ.get("OUTPUT_PATH", "output/room0")
    )
    extra_args = input_data.get("extra_args", [])
    if isinstance(extra_args, str):
        extra_args = shlex.split(extra_args)

    command = [
        "python",
        "-W",
        "ignore",
        script,
        "--dataset_path",
        dataset_path,
        "--config",
        config,
        "--output_path",
        output_path,
    ]
    if input_data.get("rerun_viewer"):
        command.append("--rerun_viewer")
    return command + list(extra_args)


def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    input_data = event.get("input", {})
    command = _build_command(input_data)
    output_path = input_data.get(
        "output_path", os.environ.get("OUTPUT_PATH", "output/room0")
    )

    os.makedirs(output_path, exist_ok=True)
    result = subprocess.run(
        command,
        cwd="/home/GS_ICP_SLAM",
        capture_output=True,
        text=True,
    )

    return {
        "command": command,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "output_path": output_path,
    }


runpod.serverless.start({"handler": handler})
