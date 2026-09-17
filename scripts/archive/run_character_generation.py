
import os
import re
import json
import time
import requests
from PIL import Image
from io import BytesIO

# --- Image Gen Function (from generate_image.py) ---
def generate_image(
    prompt: str,
    output_path: str,
    model: str = "Tongyi-MAI/Z-Image-Turbo",
    api_key: str | None = None,
    poll_interval: int = 5,
    max_wait: int = 300,
) -> str:
    base_url = "https://api-inference.modelscope.cn/"
    
    # Get API key from the explicit argument or environment.
    api_key = api_key or os.environ.get("MODELSCOPE_API_KEY", "")
    if not api_key:
        raise RuntimeError("MODELSCOPE_API_KEY is required")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Build request payload
    payload = {
        "model": model,
        "prompt": prompt,
    }

    print(f"Submitting generation for: {output_path}...")
    # Submit async generation request
    try:
        response = requests.post(
            f"{base_url}v1/images/generations",
            headers={**headers, "X-ModelScope-Async-Mode": "true"},
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        )
        response.raise_for_status()
        task_id = response.json()["task_id"]
        print(f"Task submitted: {task_id}")
    except Exception as e:
        print(f"Failed to submit task: {e}")
        return None

    # Poll for completion
    start_time = time.time()
    while True:
        if time.time() - start_time > max_wait:
            print(f"Timeout waiting for {output_path}")
            return None

        try:
            result = requests.get(
                f"{base_url}v1/tasks/{task_id}",
                headers={**headers, "X-ModelScope-Task-Type": "image_generation"},
            )
            result.raise_for_status()
            data = result.json()

            status = data["task_status"]
            if status == "SUCCEED":
                image_url = data["output_images"][0]
                image_response = requests.get(image_url)
                image_response.raise_for_status()
                image = Image.open(BytesIO(image_response.content))
                image.save(output_path)
                print(f"Image saved to: {output_path}")
                return output_path
            elif status == "FAILED":
                print(f"Generation failed for {output_path}")
                return None
            
            # print(f"Status: {status}, waiting...")
            time.sleep(poll_interval)
        except Exception as e:
            print(f"Error polling status: {e}")
            time.sleep(poll_interval)

# --- Parsing Logic ---

def parse_prompts(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by headers like ## Name
    sections = re.split(r'^##\s+(.+)$', content, flags=re.MULTILINE)
    
    characters = {}
    
    # sections[0] is intro text usually
    # sections[1] is name, sections[2] is content, sections[3] is name...
    for i in range(1, len(sections), 2):
        name_raw = sections[i].strip()
        # Clean name (remove parenthesis often used for aliases in headers if simple filename desired, but keeping full name is fine)
        # Assuming format "Name" or "Name (Alias)"
        # Let's simple use the full string but sanitize for filename
        
        body = sections[i+1]
        
        # Extract content within ```markdown ... ``` or just the text if code block not strictly followed
        # The file uses ```markdown ... ```
        match = re.search(r'```markdown\s+(.+?)\s+```', body, re.DOTALL)
        if match:
            prompt_text = match.group(1).strip()
            characters[name_raw] = prompt_text
        else:
            print(f"Warning: No markdown code block found for {name_raw}")

    return characters

def sanitize_filename(name):
    # Remove special chars
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    # Replace spaces with underscore
    name = name.replace(" ", "_").replace("（", "_").replace("）", "")
    return name

def main():
    prompts_file = "character_prompts.md"
    characters = parse_prompts(prompts_file)
    
    print(f"Found {len(characters)} characters.")
    
    output_dir = "images/characters"
    os.makedirs(output_dir, exist_ok=True)
    
    # Process all characters
    count = 0
    # To avoid rate limits or overwhelming the user, maybe we do them strictly sequentially.
    # The user asked to generate images.
    
    for name, prompt in characters.items():
        count += 1
        safe_name = sanitize_filename(name)
        filename = f"{output_dir}/{safe_name}.jpg"
        
        if os.path.exists(filename):
            print(f"Skipping {name}, {filename} already exists.")
            continue
            
        print(f"[{count}/{len(characters)}] Generating image for {name}...")
        
        # Construct the prompt. 
        # The prompt in the file is already a full description.
        # We might want to remove the "Visuals:", "Props:" labels if they confuse the model,
        # but usually they are fine or even helpful.
        # However, the file format is:
        # Style: ...
        # Character: ...
        # Visuals: ...
        # Props: ...
        # Atmosphere: ...
        
        # We can pass it as is.
        
        result = generate_image(prompt, filename)
        
        if result:
            print(f"Success: {name}")
        else:
            print(f"Failed: {name}")
            
        # Small delay
        time.sleep(2)

if __name__ == "__main__":
    main()
