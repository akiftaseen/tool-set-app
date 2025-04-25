# cleanup_subthemes.py
"""
This script deduplicates Subtheme entries in the database. For each (theme_id, name) group with multiple records,
it keeps the one with the smallest id, reassigns all Category.subtheme_id references to that id,
and deletes the duplicate Subtheme rows.
"""
from app import db, Subtheme, Category
from sqlalchemy import func

def cleanup_duplicates():
    # Find subtheme groups having duplicates
    duplicates = (
        db.session.query(
            Subtheme.theme_id,
            Subtheme.name,
            func.count(Subtheme.id).label('cnt')
        )
        .group_by(Subtheme.theme_id, Subtheme.name)
        .having(func.count(Subtheme.id) > 1)
        .all()
    )
    for theme_id, name, cnt in duplicates:
        subs = (
            Subtheme.query
            .filter_by(theme_id=theme_id, name=name)
            .order_by(Subtheme.id)
            .all()
        )
        keep = subs[0]
        dupes = subs[1:]
        for dup in dupes:
            # Reassign categories referencing the duplicate to the kept subtheme
            Category.query.filter_by(subtheme_id=dup.id).update({'subtheme_id': keep.id})
        # Delete duplicate subthemes
        for dup in dupes:
            db.session.delete(dup)
    db.session.commit()

if __name__ == '__main__':
    cleanup_duplicates()
    print("Duplicate subthemes cleaned up")
