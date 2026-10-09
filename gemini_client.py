import os
import time
import uuid
import httpx
from pathlib import Path
from typing import Optional
from google import genai
from google.genai import types
from google.genai.errors import ClientError

from config import (
    GEMINI_API_KEY,
    GEMINI_VEO_MODEL,
    GEMINI_VEO_FAST_MODEL,
    GEMINI_IMAGE_MODEL,
    GEMINI_FALLBACK_IMAGE_MODEL,
    KIE_AI_API_KEY,
    IMAGES_DIR,
    VIDEOS_DIR
)

def get_gemini_client() -> genai.Client:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in environment or .env file.")
    return genai.Client(api_key=GEMINI_API_KEY)

def resolve_image_file(image_path_or_url: str) -> Path:
    """Ensure image is locally available, downloading if it is an HTTP URL."""
    path = Path(image_path_or_url)
    if path.exists():
        return path

    if image_path_or_url.startswith("http://") or image_path_or_url.startswith("https://"):
        local_name = f"ref_{uuid.uuid4().hex[:8]}.jpg"
        local_path = IMAGES_DIR / local_name
        response = httpx.get(image_path_or_url, follow_redirects=True, timeout=30.0)
        response.raise_for_status()
        with open(local_path, "wb") as f:
            f.write(response.content)
        return local_path

    raise FileNotFoundError(f"Image source not found: {image_path_or_url}")

def generate_nano_image_kie_fallback(prompt: str, reference_image_url: str, output_path: Path) -> Path:
    """Fallback generator for Nano Image using Kie.ai if Gemini image quota is restricted."""
    if not KIE_AI_API_KEY:
        raise RuntimeError("KIE_AI_API_KEY not configured for Kie.ai fallback.")

    import re
    clean_prompt = re.sub(r"[\r\n\"“”]", " ", prompt).strip()
    clean_prompt = re.sub(r"\s+", " ", clean_prompt)

    headers = {
        "Authorization": f"Bearer {KIE_AI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "google/nano-banana-edit",
        "input": {
            "prompt": clean_prompt,
            "image_urls": [reference_image_url],
            "output_format": "png",
            "image_size": "9:16"
        }
    }
    res = httpx.post("https://api.kie.ai/api/v1/jobs/createTask", json=payload, headers=headers, timeout=30.0)
    res.raise_for_status()
    data = res.json().get("data") or {}
    task_id = data.get("taskId")
    if not task_id:
        raise RuntimeError(f"Kie.ai did not return a taskId: {res.text}")

    # Poll Kie.ai
    for _ in range(30):
        time.sleep(5)
        check = httpx.get(f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}", headers=headers, timeout=20.0)
        check_data = check.json().get("data") or {}
        if check_data.get("state") == "success":
            import json
            result_json = json.loads(check_data.get("resultJson", "{}"))
            img_url = result_json.get("resultUrls", [])[0]
            img_res = httpx.get(img_url, timeout=30.0)
            with open(output_path, "wb") as f:
                f.write(img_res.content)
            return output_path

    raise TimeoutError("Kie.ai Nano Image task timed out.")

def generate_nano_image(
    prompt: str,
    reference_image_path: Optional[str] = None,
    output_filename: Optional[str] = None
) -> str:
    """
    Generate or edit an image using Google GenAI SDK (models/nano-banana-pro-preview or gemini-2.5-flash-image).
    Falls back gracefully if free tier quota is 0 on Gemini API.
    """
    client = get_gemini_client()
    filename = output_filename or f"nano_{uuid.uuid4().hex[:8]}.png"
    output_path = IMAGES_DIR / filename

    ref_file = resolve_image_file(reference_image_path) if reference_image_path else None

    # Attempt with Gemini
    try:
        image_content = []
        if ref_file:
            image_content.append(types.Part.from_bytes(
                data=ref_file.read_bytes(),
                mime_type="image/jpeg"
            ))
        image_content.append(prompt)

        # Try gemini-2.5-flash-image or nano-banana-pro-preview
        response = client.models.generate_content(
            model=GEMINI_IMAGE_MODEL,
            contents=image_content
        )

        for candidate in response.candidates:
            for part in candidate.content.parts:
                if part.inline_data:
                    with open(output_path, "wb") as f:
                        f.write(part.inline_data.data)
                    return str(output_path)

        raise RuntimeError("No image data returned in Gemini response.")

    except ClientError as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            print("[Gemini Image] 429 Quota Exceeded on Gemini API.")
            if KIE_AI_API_KEY and reference_image_path:
                print("[Fallback] Routing Nano Image edit to Kie.ai...")
                return str(generate_nano_image_kie_fallback(prompt, reference_image_path, output_path))
            raise RuntimeError(
                "Gemini Image Generation requires linking a billing account to your Google AI Studio project "
                "(https://ai.google.dev/pricing). Alternatively, set KIE_AI_API_KEY in .env."
            ) from e
        raise

def generate_veo_video_kie_fallback(
    prompt: str,
    reference_image_url: str,
    output_path: Path
) -> Path:
    """Fallback generator for Veo Video using Kie.ai if Gemini API billing is not yet activated."""
    if not KIE_AI_API_KEY:
        raise RuntimeError("KIE_AI_API_KEY not configured for Kie.ai fallback.")

    import re
    clean_prompt = re.sub(r"[\r\n\"“”]", " ", prompt).strip()
    clean_prompt = re.sub(r"\s+", " ", clean_prompt)

    headers = {
        "Authorization": f"Bearer {KIE_AI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": clean_prompt,
        "imageUrls": [reference_image_url],
        "model": "veo3_fast",
        "aspectRatio": "9:16",
        "enableTranslation": True
    }
    res = httpx.post("https://api.kie.ai/api/v1/veo/generate", json=payload, headers=headers, timeout=30.0)
    res.raise_for_status()
    data = res.json().get("data") or {}
    task_id = data.get("taskId")
    if not task_id:
        raise RuntimeError(f"Kie.ai did not return a taskId: {res.text}")

    print(f"[Kie.ai] Veo task submitted: {task_id}. Polling for video completion...")
    for _ in range(60):
        time.sleep(10)
        check = httpx.get(f"https://api.kie.ai/api/v1/veo/record-info?taskId={task_id}", headers=headers, timeout=20.0)
        resp_data = check.json().get("data", {}).get("response", {})
        result_urls = resp_data.get("resultUrls", [])
        if result_urls:
            video_url = result_urls[0]
            print(f"[Kie.ai] Downloading completed video from {video_url}...")
            v_res = httpx.get(video_url, timeout=60.0)
            with open(output_path, "wb") as f:
                f.write(v_res.content)
            return output_path

    raise TimeoutError("Kie.ai Veo video generation timed out.")

def generate_veo_video(
    prompt: str,
    reference_image_path: Optional[str] = None,
    aspect_ratio: str = "9:16",
    output_filename: Optional[str] = None,
    poll_interval: int = 10
) -> str:
    """
    Generate an 8-second UGC video using Google Veo (models/veo-3.1-generate-preview or veo-3.1-fast-generate-preview).
    Downloads and returns the local path to the rendered MP4.
    """
    client = get_gemini_client()
    filename = output_filename or f"veo_{uuid.uuid4().hex[:8]}.mp4"
    output_path = VIDEOS_DIR / filename

    ref_file = resolve_image_file(reference_image_path) if reference_image_path else None

    # Prepare input source
    source_kwargs = {"prompt": prompt}
    if ref_file:
        source_kwargs["image"] = types.Image.from_file(location=str(ref_file))

    source = types.GenerateVideosSource(**source_kwargs)
    config = types.GenerateVideosConfig(
        aspect_ratio=aspect_ratio,
        resolution="720p"
    )

    try:
        print(f"[Veo 3.1] Submitting video generation request using model: {GEMINI_VEO_FAST_MODEL}...")
        operation = client.models.generate_videos(
            model=GEMINI_VEO_FAST_MODEL,
            source=source,
            config=config
        )

        print(f"[Veo 3.1] Operation started: {operation.name}. Polling status every {poll_interval}s...")
        while not operation.done:
            time.sleep(poll_interval)
            operation = client.operations.get(operation)
            print("[Veo 3.1] Still rendering video...")

        if operation.error:
            raise RuntimeError(f"Veo generation failed: {operation.error}")

        generated_videos = operation.response.generated_videos
        if not generated_videos:
            raise RuntimeError("No video returned in Veo operation response.")

        video = generated_videos[0]
        client.files.download(file=video.video)
        video.video.save(str(output_path))
        print(f"[Veo 3.1] Video saved successfully to: {output_path}")
        return str(output_path)

    except ClientError as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            print("[Veo 3.1] 429 Quota Exceeded on Gemini API.")
            if KIE_AI_API_KEY and reference_image_path:
                print("[Fallback] Routing Veo generation to Kie.ai...")
                return str(generate_veo_video_kie_fallback(prompt, reference_image_path, output_path))
            raise RuntimeError(
                "Gemini Veo 3.1 requires linking a Google Cloud billing account to your Google AI Studio project "
                "(https://ai.google.dev/pricing). Alternatively, set KIE_AI_API_KEY in .env."
            ) from e
        raise
