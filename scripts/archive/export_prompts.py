
import pandas as pd

# Load data
file_path = "/Users/shushu/剑来/人物设计图/《剑来》人物视觉设定档案1.xlsx"
df = pd.read_excel(file_path).fillna('')

# Style Prompt
style_prompt = "Style: Traditional Chinese ink painting style (High-quality Shuimo) combined with modern digital fantasy aesthetics. Bold, clean line art outlines contrasting with soft ink washes. Ethereal and mystical atmosphere. Golden swirling spiritual energy (Qi) flowing around. Masterpiece, 8k resolution. Aspect Ratio: 3:4."

md_content = "# Jianlai Character Prompts\n\n"

for index, row in df.iterrows():
    name = row['人物名称']
    face = row['面相与精气神']
    clothes = row['衣冠服饰细节']
    props = row['关键器物与法宝']
    atmosphere = row['气象与意境描述']
    
    # Simple cleaning: remove citations like '1-17' if possible, but regex might be overkill for now.
    # We will format it as a block.
    
    md_content += f"## {name}\n\n"
    md_content += "```markdown\n"
    md_content += f"{style_prompt}\n\n"
    md_content += f"Character: {name} (Jianlai).\n"
    md_content += f"Visuals: {face} {clothes}\n"
    md_content += f"Props: {props}\n"
    md_content += f"Atmosphere: {atmosphere}\n"
    md_content += "```\n\n"

output_file = "/Users/shushu/剑来/character_prompts.md"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(md_content)

print(f"Exported to {output_file}")
