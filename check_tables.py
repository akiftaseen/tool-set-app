"""
This script checks the contents of the database tables directly to verify what data exists.
"""
from app import app, db, Theme, Subtheme, Category, Name

# Use Flask application context
with app.app_context():
    # Check themes
    themes = Theme.query.all()
    print(f"\nThemes in database: {len(themes)}")
    for theme in themes[:5]:  # Show first 5 for brevity
        print(f"  - ID: {theme.id}, Name: {theme.name}")
    
    # Check subthemes
    subthemes = Subtheme.query.all()
    print(f"\nSubthemes in database: {len(subthemes)}")
    for subtheme in subthemes[:5]:  # Show first 5 for brevity
        print(f"  - ID: {subtheme.id}, Name: {subtheme.name}, Theme ID: {subtheme.theme_id}")
    
    # Check categories
    categories = Category.query.all()
    print(f"\nCategories in database: {len(categories)}")
    for category in categories[:5]:  # Show first 5 for brevity
        print(f"  - ID: {category.id}, Name: {category.name}, Subtheme ID: {category.subtheme_id}")
    
    # Check names
    names = Name.query.all()
    print(f"\nNames in database: {len(names)}")
    for name in names[:5]:  # Show first 5 for brevity
        print(f"  - ID: {name.id}, Name: {name.name}")
