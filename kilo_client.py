import base64
import mimetypes
from pathlib import Path
from openai import OpenAI
from config import (
    KILO_BASE_URL,
    KILO_PROMPT_API_KEY,
    KILO_PROMPT_MODEL,
    KILO_VISION_API_KEY,
    KILO_VISION_MODEL
)
from prompts import (
    VEO_IMAGE_PROMPT_SYSTEM_PROMPT,
    VEO_VIDEO_PROMPT_SYSTEM_PROMPT,
    VEO_VIDEO_PROMPT1_SYSTEM_PROMPT,
    SORA_VIDEO_PROMPT_SYSTEM_PROMPT
)

def get_prompt_client() -> OpenAI:
    return OpenAI(
        base_url=KILO_BASE_URL,
        api_key=KILO_PROMPT_API_KEY
    )

def get_vision_client() -> OpenAI:
    return OpenAI(
        base_url=KILO_BASE_URL,
        api_key=KILO_VISION_API_KEY
    )

def call_kilo_llm(system_prompt: str, user_prompt: str) -> str:
    """Call the Kilo Code gateway with Nex AGI Nex-N2.5-Pro (reasoning disabled)."""
    client = get_prompt_client()
    response = client.chat.completions.create(
        model=KILO_PROMPT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        extra_body={"reasoning_effort": "none"}
    )
    content = response.choices[0].message.content or ""
    # Clean up formatting quotes as done in the n8n workflow
    cleaned = content.replace('"', '').replace('“', '').replace('”', '').strip()
    return cleaned

def generate_veo_direct_prompt(product: str, icp: str, features: str, setting: str) -> str:
    """Generate prompt for Veo 3.1 video directly from product photo (Veo Video Prompt1)."""
    user_prompt = f"Product: {product}\n\nProduct ICP: {icp}\n\nProduct Features: {features}\n\nVideo Setting: {setting}"
    return call_kilo_llm(VEO_VIDEO_PROMPT1_SYSTEM_PROMPT, user_prompt)

def generate_nano_image_prompt(product: str, setting: str) -> str:
    """Generate prompt for Nano image generation (Veo Image Prompt)."""
    user_prompt = f"Product: {product}\n\nImage Setting: {setting}"
    return call_kilo_llm(VEO_IMAGE_PROMPT_SYSTEM_PROMPT, user_prompt)

def generate_veo_with_image_prompt(product: str, icp: str, features: str, setting: str, image_description: str) -> str:
    """Generate prompt for Veo 3.1 video with reference image description (Veo Video Prompt)."""
    user_prompt = (
        f"Product: {product}\n\n"
        f"Product ICP: {icp}\n\n"
        f"Product Features: {features}\n\n"
        f"Video Setting: {setting}\n\n"
        f"Reference Image Description: {image_description}"
    )
    return call_kilo_llm(VEO_VIDEO_PROMPT_SYSTEM_PROMPT, user_prompt)

def generate_sora_prompt(product: str, icp: str, features: str, setting: str) -> str:
    """Generate prompt for Sora 2 video (Sora Video Prompt)."""
    user_prompt = f"Product: {product}\n\nProduct ICP: {icp}\n\nProduct Features: {features}\n\nVideo Setting: {setting}"
    return call_kilo_llm(SORA_VIDEO_PROMPT_SYSTEM_PROMPT, user_prompt)

def encode_image_to_data_url(image_path: str) -> str:
    """Convert a local image file to a base64 data URL."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type:
        mime_type = "image/jpeg"
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"

def analyze_image_with_vision(image_path_or_url: str) -> str:
    """
    Analyze image using Kilo Code Vision model (Dots Studio Dots3-Note Preview).
    Replicates the n8n 'Analyze image' node.
    """
    client = get_vision_client()

    if image_path_or_url.startswith("http://") or image_path_or_url.startswith("https://"):
        image_url = image_path_or_url
    else:
        image_url = encode_image_to_data_url(image_path_or_url)

    question = "Describe what is in the image. Describe the environment and the human who is the focus of the image, as well as what the human is holding."

    response = client.chat.completions.create(
        model=KILO_VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
    )
    return response.choices[0].message.content or ""
