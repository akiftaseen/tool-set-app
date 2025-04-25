"""
This script will reset the database tables to prepare for fresh data import.
"""
from sqlalchemy import create_engine, text

# Database connection
engine = create_engine('mysql+mysqlconnector://root:password@localhost/tool_set_db', echo=True)

# Delete data in reverse order of dependencies
with engine.begin() as conn:
    print("Clearing database tables...")
    
    # Delete from name_categories (junction table)
    conn.execute(text("DELETE FROM name_categories"))
    print("Cleared name_categories table")
    
    # Delete from categories
    conn.execute(text("DELETE FROM categories"))
    print("Cleared categories table")
    
    # Delete from subthemes
    conn.execute(text("DELETE FROM subthemes"))
    print("Cleared subthemes table")
    
    # Delete from themes
    conn.execute(text("DELETE FROM themes"))
    print("Cleared themes table")
    
    # Delete from names
    conn.execute(text("DELETE FROM names"))
    print("Cleared names table")
    
print("All tables cleared successfully. Ready for fresh data import.")
