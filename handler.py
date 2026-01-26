import base64
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import runpod

ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = ROOT_DIR / "configs/Replica/caminfo.txt"


def _decode_base64(data: str) -> bytes:
    return base64.b64decode(data.encode("utf-8"))


def _write_replica_frames(frames, dataset_dir: Path) -> None:
    images_dir = dataset_dir / "images"
    depth_dir = dataset_dir / "depth_images"
    images_dir.mkdir(parents=True, exist_ok=True)
    depth_dir.mkdir(parents=True, exist_ok=True)

    for idx, frame in enumerate(frames):
        rgb_ext = frame.get("rgb_ext", "jpg")
        depth_ext = frame.get("depth_ext", "png")
        rgb_path = images_dir / f"frame{idx:06d}.{rgb_ext}"
        depth_path = depth_dir / f"depth{idx:06d}.{depth_ext}"
        rgb_path.write_bytes(_decode_base64(frame["rgb"]))
        depth_path.write_bytes(_decode_base64(frame["depth"]))


def _write_tum_frames(frames, dataset_dir: Path) -> None:
    rgb_dir = dataset_dir / "rgb"
    depth_dir = dataset_dir / "depth"
    rgb_dir.mkdir(parents=True, exist_ok=True)
    depth_dir.mkdir(parents=True, exist_ok=True)

    for idx, frame in enumerate(frames):
        rgb_ext = frame.get("rgb_ext", "png")
        depth_ext = frame.get("depth_ext", "png")
        rgb_path = rgb_dir / f"{idx:06d}.{rgb_ext}"
        depth_path = depth_dir / f"{idx:06d}.{depth_ext}"
        rgb_path.write_bytes(_decode_base64(frame["rgb"]))
        depth_path.write_bytes(_decode_base64(frame["depth"]))


def _prepare_dataset(input_payload, work_dir: Path) -> Path:
    if input_payload.get("dataset_path"):
        return Path(input_payload["dataset_path"])

    if input_payload.get("dataset_zip"):
        zip_bytes = _decode_base64(input_payload["dataset_zip"])
        zip_path = work_dir / "dataset.zip"
        zip_path.write_bytes(zip_bytes)
        extract_dir = work_dir / "dataset"
        with zipfile.ZipFile(zip_path, "r") as zip_file:
            zip_file.extractall(extract_dir)
        subdir = input_payload.get("zip_subdir")
        return extract_dir / subdir if subdir else extract_dir

    frames = input_payload.get("frames")
    if not frames:
        raise ValueError("Provide dataset_path, dataset_zip, or frames.")

    dataset_dir = work_dir / "dataset"
    camera_type = input_payload.get("camera_type", "tum")
    if camera_type == "replica":
        _write_replica_frames(frames, dataset_dir)
    elif camera_type == "tum":
        _write_tum_frames(frames, dataset_dir)
    else:
        raise ValueError("camera_type must be 'replica' or 'tum'.")
    return dataset_dir


def _collect_artifacts(output_path: Path) -> list[dict]:
    artifacts = []
    if not output_path.exists():
        return artifacts
    for root, _, files in os.walk(output_path):
        for filename in files:
            file_path = Path(root) / filename
            artifacts.append(
                {
                    "path": str(file_path),
                    "size_bytes": file_path.stat().st_size,
                }
            )
    return artifacts


def handler(job):
    input_payload = job.get("input", {})
    work_dir = Path(tempfile.mkdtemp(prefix="gs-icp-slam-"))
    output_path = Path(
        input_payload.get("output_path", work_dir / "output")
    )
    output_path.mkdir(parents=True, exist_ok=True)
    dataset_path = _prepare_dataset(input_payload, work_dir)

    config_path = Path(input_payload.get("config", DEFAULT_CONFIG))
    args = [
        "python",
        "gs_icp_slam.py",
        "--dataset_path",
        str(dataset_path),
        "--config",
        str(config_path),
        "--output_path",
        str(output_path),
    ]

    extra_args = input_payload.get("extra_args")
    if extra_args:
        if not isinstance(extra_args, list):
            raise ValueError("extra_args must be a list of CLI arguments.")
        args.extend(extra_args)

    result = subprocess.run(
        args,
        cwd=str(ROOT_DIR),
        check=False,
        capture_output=True,
        text=True,
    )

    response = {
        "return_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "output_path": str(output_path),
        "artifacts": _collect_artifacts(output_path),
    }

    if input_payload.get("cleanup", True):
        shutil.rmtree(work_dir, ignore_errors=True)

    if result.returncode != 0:
        raise RuntimeError(json.dumps(response))

    return response


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
