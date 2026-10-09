import traceback
from typing import Dict, Any
from database import update_task_fields
import kilo_client
import gemini_client

def process_task(task: Dict[str, Any]):
    """
    Execute the end-to-end UGC ad generation pipeline for a single task.
    Replicates the n8n workflow logic with exact prompt engineering and branching.
    """
    task_id = task["id"]
    model_choice = task.get("model", "Veo 3.1").strip()
    product = task["product"]
    photo = task["product_photo"]
    icp = task["icp"]
    features = task["product_features"]
    setting = task["video_setting"]

    print(f"\n[Pipeline] Starting Task #{task_id} - Model: '{model_choice}' for Product: '{product}'")
    update_task_fields(task_id, status="Processing", error_message=None)

    try:
        if model_choice == "Veo 3.1":
            # --- Branch 1: Veo 3.1 Direct ---
            print("[Step 1/2] Generating Veo direct prompt via Kilo Code (Nex AGI)...")
            veo_prompt = kilo_client.generate_veo_direct_prompt(product, icp, features, setting)
            update_task_fields(task_id, prompt_video=veo_prompt)
            print(f"[Step 1/2] Prompt: {veo_prompt[:120]}...")

            print("[Step 2/2] Generating Veo video via Google GenAI...")
            video_path = gemini_client.generate_veo_video(
                prompt=veo_prompt,
                reference_image_path=photo,
                aspect_ratio="9:16"
            )
            update_task_fields(task_id, finished_video_path=video_path, status="Finished")
            print(f"[Pipeline] Task #{task_id} finished successfully! Video: {video_path}")

        elif model_choice == "Nano + Veo 3.1":
            # --- Branch 2: Nano Image Edit + Vision Analysis + Veo 3.1 ---
            print("[Step 1/5] Generating Nano image prompt via Kilo Code...")
            image_prompt = kilo_client.generate_nano_image_prompt(product, setting)
            update_task_fields(task_id, prompt_image=image_prompt)
            print(f"[Step 1/5] Image Prompt: {image_prompt[:120]}...")

            print("[Step 2/5] Generating Nano image via Google GenAI...")
            image_path = gemini_client.generate_nano_image(image_prompt, reference_image_path=photo)
            update_task_fields(task_id, generated_image_path=image_path)
            print(f"[Step 2/5] Nano image created: {image_path}")

            print("[Step 3/5] Analyzing generated image via Kilo Code Vision (Dots Studio)...")
            analysis = kilo_client.analyze_image_with_vision(image_path)
            update_task_fields(task_id, image_analysis=analysis)
            print(f"[Step 3/5] Vision Analysis: {analysis[:120]}...")

            print("[Step 4/5] Generating Veo video prompt with vision context...")
            veo_prompt = kilo_client.generate_veo_with_image_prompt(
                product, icp, features, setting, analysis
            )
            update_task_fields(task_id, prompt_video=veo_prompt)
            print(f"[Step 4/5] Video Prompt: {veo_prompt[:120]}...")

            print("[Step 5/5] Generating Veo video with edited image...")
            video_path = gemini_client.generate_veo_video(
                prompt=veo_prompt,
                reference_image_path=image_path,
                aspect_ratio="9:16"
            )
            update_task_fields(task_id, finished_video_path=video_path, status="Finished")
            print(f"[Pipeline] Task #{task_id} finished successfully! Video: {video_path}")

        elif model_choice == "Sora 2":
            # --- Branch 3: Sora 2 Video ---
            print("[Step 1/2] Generating Sora prompt via Kilo Code...")
            sora_prompt = kilo_client.generate_sora_prompt(product, icp, features, setting)
            update_task_fields(task_id, prompt_video=sora_prompt)
            print(f"[Step 1/2] Sora Prompt: {sora_prompt[:120]}...")

            print("[Step 2/2] Rendering video with Veo/Sora...")
            video_path = gemini_client.generate_veo_video(
                prompt=sora_prompt,
                reference_image_path=photo,
                aspect_ratio="9:16"
            )
            update_task_fields(task_id, finished_video_path=video_path, status="Finished")
            print(f"[Pipeline] Task #{task_id} finished successfully! Video: {video_path}")

        else:
            raise ValueError(f"Unknown model choice: {model_choice}. Use 'Veo 3.1', 'Nano + Veo 3.1', or 'Sora 2'.")

    except Exception as e:
        err_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        print(f"[Pipeline Error] Task #{task_id} failed: {e}")
        update_task_fields(task_id, status="Failed", error_message=err_msg)
