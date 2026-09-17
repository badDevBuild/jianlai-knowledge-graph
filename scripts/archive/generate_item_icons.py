import requests
import json
import base64
import os
import time

# === Configuration ===
BASE_URL = "http://127.0.0.1:7861"
API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL_NAME = "gemini-3-pro-image"
ITEMS_FILE = "frontend/public/data/items.json"
IMAGE_DIR = "frontend/public/images/items"

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def save_base64_image(base64_str, filename):
    try:
        if "," in base64_str:
            base64_str = base64_str.split(",")[1]
        img_data = base64.b64decode(base64_str)
        with open(filename, 'wb') as f:
            f.write(img_data)
        print(f"✅ Image saved: {filename}")
        return True
    except Exception as e:
        print(f"❌ Failed to save image: {e}")
        return False

def generate_icon(item_name, description):
    print(f"🎨 Generating icon for: {item_name}...")
    url = f"{BASE_URL}/antigravity/v1/models/{MODEL_NAME}:generateContent"
    headers = {
        "x-goog-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Construct Prompt
    prompt = f"A high quality fantasy RPG icon of {item_name}. Description: {description}. Style: Digital art, detailed game asset, centered, isolated on neutral dark background, magical atmosphere."
    
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "image_config": {
                "aspect_ratio": "1:1"
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            if "response" in result: result = result["response"]
            
            candidates = result.get('candidates', [])
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                for part in parts:
                    if 'inlineData' in part:
                        return part['inlineData']['data']
            print("⚠️ No image data found in response.")
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Request Error: {e}")
    
    return None

def run():
    ensure_dir(IMAGE_DIR)
    
    print(f"📂 Loading items from {ITEMS_FILE}...")
    with open(ITEMS_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)
    
    # Get next batch of items without icons
    batch_size = 50
    items_to_process = []
    
    for key, data in items.items():
        if "icon" not in data:
            items_to_process.append(key)
            if len(items_to_process) >= batch_size:
                break
                
    print(f"🎯 Found {len(items_to_process)} items needing icons (limit {batch_size})...")
    
    updated_count = 0
    for key in items_to_process:
        item = items[key]
        item_name = item["name"]
        
        # Check if icon already exists to avoid re-generating (optional, but good for testing)
        # For this task, we overwrite or create.
        
        desc = item.get("description", "")
        # Limit description length for prompt
        short_desc = desc[:100] + "..." if len(desc) > 100 else desc
        
        base64_data = generate_icon(item_name, short_desc)
        
        if base64_data:
            filename = f"{key}.png"
            filepath = os.path.join(IMAGE_DIR, filename)
            if save_base64_image(base64_data, filepath):
                # Update item data
                # Relative path for frontend
                item["icon"] = f"/jianlai/images/items/{filename}"
                updated_count += 1
        
        # Rate limit friendly
        time.sleep(2)
        
    if updated_count > 0:
        print(f"💾 Updating {ITEMS_FILE} with {updated_count} new icons...")
        with open(ITEMS_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        print("🎉 Done!")
    else:
        print("⚠️ No icons generated.")

if __name__ == "__main__":
    run()
