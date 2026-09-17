
import pandas as pd

file_path = "/Users/shushu/剑来/人物设计图/《剑来》人物视觉设定档案1.xlsx"
df = pd.read_excel(file_path)
print(f"Total rows: {len(df)}")
print("Names:", df['人物名称'].tolist())
