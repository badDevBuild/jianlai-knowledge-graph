import json
import re
import os

def parse_appearance(text):
    """
    Parses the appearance text into a dictionary of fields.
    Expected format segments: Context: ..., Face: ..., Body: ..., Clothing: ..., Aura: ...
    """
    data = {}
    # Split by the known keys, capturing the delimiters
    parts = re.split(r'(Context:|Face:|Body:|Clothing:|Aura:)', text)
    
    # parts[0] is usually empty or text before the first key
    # parts[1] is the first key, parts[2] is the first value, etc.
    
    current_key = None
    for item in parts:
        if item.endswith(':'):
            current_key = item.strip(':')
        elif current_key:
            # This is a value part, cleanup and append
            val = item.strip()
            if val:
                # If we already extracted this key (duplicate), append (though unlikely with this regex split)
                if current_key in data:
                    data[current_key] += " " + val
                else:
                    data[current_key] = val
    return data

def main():
    input_path = 'data/build/all_appearances.json'
    output_path = 'data/build/character_image_prompts.json'
    
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    print(f"Reading appearances from {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        appearances = json.load(f)
        
    prompts = {}
    
    for name, desc in appearances.items():
        parsed = parse_appearance(desc)
        
        # --- Prompt Construction Strategy ---
        # Target Style:
        # 主体: [Name]。 [Context]
        # 风格: 剑来仙侠风格, 东方古典水墨, 极致细腻, 史诗感
        # 视觉外观: [Face]。 [Body]。 [Clothing]
        # 动态特效: [Aura]
        # 背景描述: 古典仙侠意境, 朦胧山水背景 (Placeholder/Generic)
        # 画面质感: 8k分辨率, 细节丰富, 水墨晕染
        
        context = parsed.get("Context", "").replace('\n', ' ')
        face = parsed.get("Face", "").replace('\n', ' ')
        body = parsed.get("Body", "").replace('\n', ' ')
        clothing = parsed.get("Clothing", "").replace('\n', ' ')
        aura = parsed.get("Aura", "").replace('\n', ' ')
        
        prompt_parts = []
        
        # 1. 主体 (Subject)
        prompt_parts.append(f"主体: {name}。 {context}")
        
        # 2. 风格 (Style)
        prompt_parts.append("风格: 东方古典仙侠风格, 东方古典水墨, 极致细腻, 史诗感")
        
        # 3. 视觉外观 (Visual Appearance)
        # Combine Face, Body, Clothing
        visuals = []
        if face and face != "未知": visuals.append(face)
        if body and body != "未知": visuals.append(body)
        if clothing and clothing != "未知": visuals.append(clothing)
        
        visual_str = "。 ".join(visuals)
        if not visual_str:
            visual_str = "仙侠人物形象"
        prompt_parts.append(f"视觉外观: {visual_str}")
        
        # 4. 动态特效 (Dynamic Effects)
        if aura and aura != "未知":
            prompt_parts.append(f"动态特效: {aura}")
        else:
             prompt_parts.append("动态特效: 灵气缭绕")

        # 5. 背景描述 (Background)
        prompt_parts.append("背景描述: 古典仙侠意境, 朦胧山水背景")
        
        # 6. 画面质感 (Texture)
        prompt_parts.append("画面质感: 8k分辨率, 细节丰富, 水墨晕染")
        
        # Join with " 。" as seen in items_prompts.json
        full_prompt = " 。".join(prompt_parts)
        
        prompts[name] = full_prompt
        
    print(f"Generating prompts for {len(prompts)} characters...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
        
    print(f"Saved prompts to {output_path}")

if __name__ == "__main__":
    main()
