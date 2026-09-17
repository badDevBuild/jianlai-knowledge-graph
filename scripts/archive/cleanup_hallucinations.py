
import json
import os
import glob

INPUT_DIR = 'data/build/profiles_v3'

def cleanup():
    files = glob.glob(os.path.join(INPUT_DIR, '*.json'))
    print(f"Scanning {len(files)} profiles for hallucinations...")
    
    deleted_count = 0
    hallucinated_files = []
    
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            name = data.get('name', '')
            
            # Check for the specific hallucination marker from NotebookLM
            if '推测为' in name or '推测' in name or '用户查询' in name:
                hallucinated_files.append((filepath, name))
                
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            
    print(f"Found {len(hallucinated_files)} potential duplicates/hallucinations:")
    print("-" * 50)
    print(f"{'Filename':<30} | {'Internal Name Detected'}")
    print("-" * 50)
    
    for filepath, name in hallucinated_files:
        filename = os.path.basename(filepath)
        clean_name = name.replace('\n', ' ')
        print(f"Deleting {filename:<30} | {clean_name}")
        os.remove(filepath)
        deleted_count += 1
        
    print("-" * 50)
    print(f"Cleanup complete. Deleted {deleted_count} files.")

if __name__ == "__main__":
    cleanup()
