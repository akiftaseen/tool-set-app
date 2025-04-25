"""
This script examines the structure of the Excel file to understand how themes, subthemes, and categories are organized.
"""
import pandas as pd

# Read Excel file
df = pd.read_excel('tool_set.xlsx', header=[0, 1, 2], index_col=0)

# Print basic info about the dataframe
print("Excel file information:")
print(f"Shape: {df.shape}")
print(f"Index (first 5): {df.index[:5].tolist()}")
print(f"Column levels: {df.columns.nlevels}")

# Examine each level of the multi-index columns
print("\nColumn levels content:")
for level in range(df.columns.nlevels):
    level_values = df.columns.get_level_values(level)
    unique_values = sorted(list(set(v for v in level_values if pd.notna(v))))
    print(f"Level {level} unique values ({len(unique_values)}): {unique_values[:10]}...")
    
    # Count occurrences of each value at this level
    value_counts = {}
    for value in level_values:
        if pd.notna(value):
            if value not in value_counts:
                value_counts[value] = 0
            value_counts[value] += 1
    
    # Print the top 5 most common values
    print("Top 5 most common values:")
    for value, count in sorted(value_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  '{value}': {count} occurrences")

# Print a sample of the full column headers to see the hierarchy
print("\nColumn headers sample (first 10):")
for i, col in enumerate(df.columns[:10]):
    theme, subtheme, category = col
    print(f"Column {i}: Theme='{theme}', Subtheme='{subtheme}', Category='{category}'")

# Try to identify the real subtheme names
print("\nAnalyzing theme-subtheme relationships:")
theme_subtheme_map = {}
for col in df.columns:
    theme, subtheme, category = col
    if pd.notna(theme) and pd.notna(subtheme):
        if theme not in theme_subtheme_map:
            theme_subtheme_map[theme] = set()
        theme_subtheme_map[theme].add(subtheme)

for theme, subthemes in theme_subtheme_map.items():
    print(f"Theme '{theme}' has {len(subthemes)} subtheme(s): {sorted(list(subthemes))}")
