from app import db, Theme, Subtheme, Category, Name

print("\n--- Database Statistics ---")
print(f"Number of themes: {Theme.query.count()}")
print(f"Number of subthemes: {Subtheme.query.count()}")
print(f"Number of categories: {Category.query.count()}")
print(f"Number of names: {Name.query.count()}")

print("\n--- First 5 Themes ---")
themes = Theme.query.limit(5).all()
if themes:
    for theme in themes:
        print(f"ID: {theme.id}, Name: {theme.name}")
else:
    print("No themes found in the database.")
