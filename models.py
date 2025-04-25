\
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy here
db = SQLAlchemy()

# --- Define Models ---
class Theme(db.Model):
    __tablename__ = 'themes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    subthemes = db.relationship('Subtheme', backref='theme')

class Subtheme(db.Model):
    __tablename__ = 'subthemes'
    id = db.Column(db.Integer, primary_key=True)
    theme_id = db.Column(db.Integer, db.ForeignKey('themes.id'))
    name = db.Column(db.String(255))
    categories = db.relationship('Category', backref='subtheme')

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    subtheme_id = db.Column(db.Integer, db.ForeignKey('subthemes.id'))
    name = db.Column(db.String(255))
    names = db.relationship('Name', secondary='name_categories', back_populates='categories')

class Name(db.Model):
    __tablename__ = 'names'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    categories = db.relationship('Category', secondary='name_categories', back_populates='names')

class NameCategory(db.Model):
    __tablename__ = 'name_categories'
    name_id = db.Column(db.Integer, db.ForeignKey('names.id'), primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), primary_key=True)
