
import pandas as pd
import sys

try:
    file_path = "/Users/shushu/剑来/人物设计图/《剑来》人物视觉设定档案1.xlsx"
    df = pd.read_excel(file_path)
    print("Columns:", df.columns.tolist())
    print("-" * 20)
    print("First 5 rows:")
    print(df.head(5).to_string())
except Exception as e:
    print(f"Error: {e}")
