import pandas as pd
import logging

# Import your db object and models
from models import db, Theme, Subtheme, Category, Name, NameCategory
from config import DATABASE_URL

def safe_str(val):
    return str(val).strip() if not pd.isna(val) else ""

def populate_db_from_excel(app_instance):
    """Reads data from tool_set.xlsx and populates the database."""
    logging.info("Starting database population from tool_set.xlsx…")
    
    try:
        with app_instance.app_context():
            logging.info("Reading tool_set.xlsx with 3 header rows…")
            try:
                df = pd.read_excel(
                    'tool_set.xlsx',
                    sheet_name=0,
                    header=[0, 1, 2],
                    index_col=0,
                    engine='openpyxl'
                )
                # rename the column‐index levels for clarity
                df.columns.names = ['theme', 'subtheme', 'category']
                logging.info("Excel file read successfully.")
                logging.debug(f"Columns MultiIndex levels: {df.columns.names}")
                logging.debug(f"Sample (first 5 rows):\n{df.head()}")
            except FileNotFoundError:
                logging.error("Error: tool_set.xlsx not found.")
                return
            except Exception as e:
                logging.error("Error reading tool_set.xlsx", exc_info=True)
                return

            # caches to avoid re‐queries
            themes_cache = {}
            subthemes_cache = {}
            categories_cache = {}
            names_cache = {}

            # process each (theme, subtheme, category) triple
            for theme_name, subtheme_name, category_name in df.columns:
                theme_key, subtheme_key = safe_str(theme_name), safe_str(subtheme_name)
                category_key = safe_str(category_name)
                if not (theme_key and subtheme_key and category_key):
                    continue

                # → Theme
                theme = themes_cache.get(theme_key)
                if not theme:
                    theme = (db.session.query(Theme)
                                    .filter_by(name=theme_key)
                                    .first())
                    if not theme:
                        theme = Theme(name=theme_key)
                        db.session.add(theme)
                        db.session.flush()
                    themes_cache[theme_key] = theme

                # → Subtheme
                st_key = (theme.id, subtheme_key)
                subtheme = subthemes_cache.get(st_key)
                if not subtheme:
                    subtheme = (db.session.query(Subtheme)
                                       .filter_by(theme_id=theme.id, name=subtheme_key)
                                       .first())
                    if not subtheme:
                        subtheme = Subtheme(theme_id=theme.id, name=subtheme_key)
                        db.session.add(subtheme)
                        db.session.flush()
                    subthemes_cache[st_key] = subtheme

                # → Category
                cat_key = (subtheme.id, category_key)
                category = categories_cache.get(cat_key)
                if not category:
                    category = (db.session.query(Category)
                                        .filter_by(subtheme_id=subtheme.id, name=category_key)
                                        .first())
                    if not category:
                        category = Category(subtheme_id=subtheme.id, name=category_key)
                        db.session.add(category)
                        db.session.flush()
                    categories_cache[cat_key] = category

                # → Names & Associations
                # iterate each row; if the cell is non‐NA, treat the row‐index as the name
                series = df[(theme_name, subtheme_name, category_name)]
                for row_index, cell_value in series.items():
                    if pd.isna(cell_value):
                        continue
                    name_str = safe_str(row_index)
                    if not name_str:
                        continue

                    # get or create Name
                    name_obj = names_cache.get(name_str)
                    if not name_obj:
                        name_obj = (db.session.query(Name)
                                         .filter_by(name=name_str)
                                         .first())
                        if not name_obj:
                            name_obj = Name(name=name_str)
                            db.session.add(name_obj)
                            db.session.flush()
                        names_cache[name_str] = name_obj

                    # link Name ↔ Category
                    exists = (db.session.query(NameCategory)
                                     .filter_by(name_id=name_obj.id, category_id=category.id)
                                     .first())
                    if not exists:
                        db.session.add(
                            NameCategory(name_id=name_obj.id, category_id=category.id)
                        )

            # commit everything once
            logging.info("Committing to the database…")
            db.session.commit()
            logging.info("Done populating database.")

    except Exception as e:
        logging.error("Unexpected error during DB population", exc_info=True)
        db.session.rollback()

if __name__ == '__main__':
    from app import app as flask_app
    logging.basicConfig(level=logging.INFO)
    print("Running as script…")
    populate_db_from_excel(flask_app)
    print("Finished.")