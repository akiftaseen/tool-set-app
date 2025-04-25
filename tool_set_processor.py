import pandas as pd
import logging

# Import db object and models from models.py
from models import db, Theme, Subtheme, Category, Name, NameCategory
from config import DATABASE_URL # Use the same config as the app

def safe_str(val):
    return str(val).strip() if not pd.isna(val) else ""

def populate_db_from_excel(app_instance):
    """Reads data from tool_set.xlsx and populates the database."""
    logging.info("Starting database population from tool_set.xlsx...")
    
    try:
        # Use the app's context to work with the database session
        with app_instance.app_context():
            # Check if data already exists (simple check on themes)
            if db.session.query(Theme).first():
                logging.info("Database already contains data. Skipping population.")
                return

            logging.info("Reading tool_set.xlsx...")
            try:
                df = pd.read_excel('tool_set.xlsx', header=[0, 1, 2], index_col=0)
                logging.info("Excel file read successfully.")
            except FileNotFoundError:
                logging.error("Error: tool_set.xlsx not found. Cannot populate database.")
                return
            except Exception as e:
                logging.error(f"Error reading tool_set.xlsx: {e}", exc_info=True)
                return

            # --- Data Processing --- 
            themes_cache = {}
            subthemes_cache = {}
            categories_cache = {}
            names_cache = {}

            logging.info("Processing Excel data and inserting into database...")
            for col in df.columns:
                theme_name, subtheme_name_orig, category_name = col
                theme_name = safe_str(theme_name)
                subtheme_name_orig = safe_str(subtheme_name_orig)
                category_name = safe_str(category_name)
                # Skip if any part of the hierarchy is empty after conversion
                if not theme_name or not subtheme_name_orig or not category_name:
                    continue

                # --- Theme --- 
                theme = themes_cache.get(theme_name)
                if not theme:
                    theme = db.session.query(Theme).filter_by(name=theme_name).first()
                    if not theme:
                        theme = Theme(name=theme_name)
                        db.session.add(theme)
                        db.session.flush() # Flush to get the ID if needed immediately
                    themes_cache[theme_name] = theme

                # --- Subtheme --- 
                # Use a combination for uniqueness if original subtheme names are ambiguous
                subtheme_key = (theme.id, subtheme_name_orig) 
                subtheme = subthemes_cache.get(subtheme_key)
                if not subtheme:
                    subtheme = db.session.query(Subtheme).filter_by(theme_id=theme.id, name=subtheme_name_orig).first()
                    if not subtheme:
                        subtheme = Subtheme(theme_id=theme.id, name=subtheme_name_orig)
                        db.session.add(subtheme)
                        db.session.flush()
                    subthemes_cache[subtheme_key] = subtheme

                # --- Category --- 
                category_key = (subtheme.id, category_name)
                category = categories_cache.get(category_key)
                if not category:
                    category = db.session.query(Category).filter_by(subtheme_id=subtheme.id, name=category_name).first()
                    if not category:
                        category = Category(subtheme_id=subtheme.id, name=category_name)
                        db.session.add(category)
                        db.session.flush()
                    categories_cache[category_key] = category

                # --- Names and Associations --- 
                for name_str in df[col].dropna():
                    name_str = str(name_str).strip()
                    if not name_str:
                        continue
                        
                    name_obj = names_cache.get(name_str)
                    if not name_obj:
                        name_obj = db.session.query(Name).filter_by(name=name_str).first()
                        if not name_obj:
                            name_obj = Name(name=name_str)
                            db.session.add(name_obj)
                            db.session.flush()
                        names_cache[name_str] = name_obj

                    # --- Association (NameCategory) --- 
                    # Check if association already exists
                    assoc_exists = db.session.query(NameCategory).filter_by(name_id=name_obj.id, category_id=category.id).first()
                    if not assoc_exists:
                        # Use direct insertion for composite primary key tables if merge doesn't work well
                        new_assoc = NameCategory(name_id=name_obj.id, category_id=category.id)
                        db.session.add(new_assoc)
                        # Flush periodically might be needed for very large datasets, but commit at the end is usually fine

            logging.info("Committing changes to the database...")
            db.session.commit()
            logging.info("Database population completed successfully.")

    except Exception as e:
        logging.error(f"An error occurred during database population: {e}", exc_info=True)
        db.session.rollback() # Rollback in case of error

# --- Optional: Allow running this script directly for local testing --- 
if __name__ == '__main__':
    # This requires app.py to be runnable and configured correctly
    # You might need to create a temporary Flask app instance here if running standalone
    from app import app as flask_app # Import the app instance from app.py
    logging.basicConfig(level=logging.INFO)
    print("Running tool_set_processor directly...")
    populate_db_from_excel(flask_app)
    print("Direct execution finished.")