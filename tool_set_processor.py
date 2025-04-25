import pandas as pd
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, text

# Database connection (update with your MySQL credentials)
engine = create_engine('mysql+mysqlconnector://root:password@localhost/tool_set_db', echo=True)

# Define metadata
metadata = MetaData()

# Define tables
themes = Table('themes', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String(255), unique=True, nullable=False)
)

subthemes = Table('subthemes', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('theme_id', Integer, ForeignKey('themes.id'), nullable=False),
    Column('name', String(255), nullable=False),
    mysql_engine='InnoDB'
)

categories = Table('categories', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('subtheme_id', Integer, ForeignKey('subthemes.id'), nullable=False),
    Column('name', String(255), nullable=False),
    mysql_engine='InnoDB'
)

names = Table('names', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String(255), unique=True, nullable=False)
)

name_categories = Table('name_categories', metadata,
    Column('name_id', Integer, ForeignKey('names.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True),
    mysql_engine='InnoDB'
)

# Create tables
metadata.create_all(engine)

# Read Excel file
df = pd.read_excel('tool_set.xlsx', header=[0, 1, 2], index_col=0)

# Print dataframe column headers to debug
print("Excel file column headers structure:")
print(f"Column levels: {df.columns.nlevels}")
for level in range(df.columns.nlevels):
    print(f"Level {level} unique values: {df.columns.get_level_values(level).unique().tolist()}")
print("\nDetailed column headers (all):")
for i, col in enumerate(df.columns):
    theme, subtheme, category = col
    print(f"Column {i}: Theme='{theme}', Subtheme='{subtheme}', Category='{category}'")

# Display first few rows of the DataFrame to understand structure
print("\nFirst 5 rows of the DataFrame:")
print(df.head())

# Process headers to extract themes, subthemes, and categories
column_mapping = {}
with engine.begin() as conn:  # Using begin() creates a transaction that will be committed automatically
    # Insert themes
    for theme in df.columns.get_level_values(0).unique():
        if pd.notna(theme):  # Check if theme is not NaN
            conn.execute(themes.insert().values(name=theme).prefix_with('IGNORE'))
    
    # Insert subthemes and categories
    for col in df.columns:
        theme, subtheme, category = col
        
        # Skip if any part of the hierarchy is NaN
        if pd.isna(theme) or pd.isna(subtheme) or pd.isna(category):
            print(f"Skipping column with NaN values: {col}")
            continue
        
        # Generate a meaningful subtheme name instead of using 'TE'
        # This creates a descriptive subtheme name based on theme and category
        meaningful_subtheme_name = f"{theme} - {category}"
        print(f"Processing: Theme={theme}, Original Subtheme={subtheme}, Using={meaningful_subtheme_name}, Category={category}")
        
        theme_id = conn.execute(text("SELECT id FROM themes WHERE name = :name"), {"name": theme}).scalar()
        if not theme_id:
            print(f"Warning: Theme '{theme}' not found in database")
            continue
            
        conn.execute(subthemes.insert().values(theme_id=theme_id, name=meaningful_subtheme_name).prefix_with('IGNORE'))
        subtheme_id = conn.execute(text("SELECT id FROM subthemes WHERE theme_id = :theme_id AND name = :name"), 
                                  {"theme_id": theme_id, "name": meaningful_subtheme_name}).scalar()
        if not subtheme_id:
            print(f"Warning: Subtheme '{subtheme}' not properly inserted")
            continue
            
        conn.execute(categories.insert().values(subtheme_id=subtheme_id, name=category).prefix_with('IGNORE'))
        category_id = conn.execute(text("SELECT id FROM categories WHERE subtheme_id = :subtheme_id AND name = :name"), 
                                  {"subtheme_id": subtheme_id, "name": category}).scalar()
        if not category_id:
            print(f"Warning: Category '{category}' not properly inserted")
            continue
            
        column_mapping[col] = category_id

# Insert names and their category associations
with engine.begin() as conn:  # Using begin() creates a transaction that will be committed automatically
    for name in df.index:
        conn.execute(names.insert().values(name=str(name)).prefix_with('IGNORE'))
        name_id = conn.execute(text("SELECT id FROM names WHERE name = :name"), {"name": str(name)}).scalar()
        row = df.loc[name]
        for col in df.columns:
            if row[col] == 'x':
                category_id = column_mapping[col]
                conn.execute(name_categories.insert().values(name_id=name_id, category_id=category_id).prefix_with('IGNORE'))

print("Data successfully uploaded to MySQL database.")