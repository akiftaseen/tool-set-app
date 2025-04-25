import pandas as pd

# Try basic Excel reading with error handling
try:
    print("Attempting to read the Excel file...")
    df = pd.read_excel('tool_set.xlsx', header=[0, 1, 2], index_col=0)
    print("Successfully read Excel file!")
    print(f"Shape: {df.shape}")
    print(f"Column levels: {df.columns.nlevels}")
    
    # Print the first few column headers
    print("\nSample column headers:")
    for i, col in enumerate(list(df.columns)[:5]):
        print(f"Column {i}: {col}")
        
except Exception as e:
    print(f"Error reading Excel file: {str(e)}")
    
# Try a simpler approach without multi-level headers
try:
    print("\nTrying to read without multi-level headers...")
    df_simple = pd.read_excel('tool_set.xlsx')
    print("Simple read successful!")
    print(f"Columns: {df_simple.columns.tolist()[:10]}")
    print(f"First row: {df_simple.iloc[0].tolist()[:10]}")
except Exception as e:
    print(f"Error with simple read: {str(e)}")
