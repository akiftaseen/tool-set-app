from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import random
import logging
import os
from sqlalchemy import inspect
from tool_set_processor import populate_db_from_excel

logging.basicConfig(level=logging.INFO)  # Add basic logging

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure key

# Import database configuration
from config import DATABASE_URL

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy()  # Initialize SQLAlchemy without the app first

# Models MUST be defined or imported here so SQLAlchemy knows about them
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

# Now initialize db with the app
db.init_app(app)

# Function to Create Tables
def create_tables(app_instance):
    with app_instance.app_context():
        logging.info("Inside app_context, attempting db.create_all()...")
        try:
            db.create_all()
            logging.info("db.create_all() executed.")
            inspector = inspect(db.engine)
            if inspector.has_table("themes"):
                logging.info("Verified 'themes' table exists after create_all.")
            else:
                logging.warning("WARNING: 'themes' table NOT found after create_all.")
        except Exception as e:
            logging.error(f"Error during db.create_all() inside context: {e}", exc_info=True)

# Create Tables Explicitly
logging.info("Calling create_tables function...")
create_tables(app)
logging.info("Finished calling create_tables function.")

# Populate Database from Excel
logging.info("Calling populate_db_from_excel function...")
try:
    populate_db_from_excel(app)
    logging.info("Finished calling populate_db_from_excel function.")
except Exception as e:
    logging.error(f"Error during database population: {e}", exc_info=True)

# Import and Initialize Dash App
logging.info("Importing and initializing Dash app...")
from dashboard import get_dash_app
try:
    dash_app = get_dash_app(app)  # Pass the Flask app instance
    logging.info("Dash app initialized.")
except Exception as e:
    logging.error(f"Error during Dash app initialization: {e}", exc_info=True)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Front Portal Routes
@app.route('/')
def index():
    logging.info("Accessing index route...")
    try:
        themes = Theme.query.all()
        logging.info(f"Found {len(themes)} themes.")
        return render_template('index.html', themes=themes)
    except Exception as e:
        logging.error(f"Error in index route querying themes: {e}", exc_info=True)
        return "Error loading themes. Database might not be ready.", 500

@app.route('/api/subthemes')
def get_subthemes():
    theme_id = request.args.get('theme_id')
    try:
        theme_id = int(theme_id)
    except (TypeError, ValueError):
        return jsonify([])
    subthemes = Subtheme.query.filter_by(theme_id=theme_id).all()
    response = jsonify([
        {'id': s.id, 'name': f"{s.theme.name} - {s.name}"}
        for s in subthemes
    ])
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/api/categories')
def get_categories():
    subtheme_id = request.args.get('subtheme_id')
    try:
        subtheme_id = int(subtheme_id)
    except (TypeError, ValueError):
        return jsonify([])
    categories = Category.query.filter_by(subtheme_id=subtheme_id).all()
    response = jsonify([
        {'id': c.id, 'name': f"{c.subtheme.theme.name} - {c.subtheme.name} - {c.name}"}
        for c in categories
    ])
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/api/random_name')
def get_random_name():
    category_id = request.args.get('category_id')
    category = Category.query.get(category_id)
    if category and category.names:
        random_name = random.choice(category.names)
        count = len(category.names)
        response = jsonify({'name': random_name.name, 'count': count, 
                        'theme': category.subtheme.theme.name, 
                        'subtheme': category.subtheme.name, 
                        'category': category.name})
    else:
        response = jsonify({'name': None, 'count': 0})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

# Back Portal Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['id'] == 'apple' and request.form['password'] == 'apple':
            session['logged_in'] = True
            return redirect(url_for('admin'))
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin():
    themes = Theme.query.order_by(Theme.name).all()
    subthemes = Subtheme.query.join(Theme).order_by(Theme.name, Subtheme.name).all()
    categories = Category.query.join(Category.subtheme).join(Subtheme.theme).order_by(Theme.name, Subtheme.name, Category.name).all()
    names = Name.query.order_by(Name.name).all()

    name_category_map = {}
    associations = NameCategory.query.all()
    for assoc in associations:
        if assoc.name_id not in name_category_map:
            name_category_map[assoc.name_id] = set()
        name_category_map[assoc.name_id].add(assoc.category_id)

    theme_spans = {}
    subtheme_spans = {}
    for cat in categories:
        theme_name = cat.subtheme.theme.name
        subtheme_key = f"{cat.subtheme.theme.name}-{cat.subtheme.name}"
        theme_spans[theme_name] = theme_spans.get(theme_name, 0) + 1
        subtheme_spans[subtheme_key] = subtheme_spans.get(subtheme_key, 0) + 1

    return render_template(
        'admin.html',
        themes=themes,
        subthemes=subthemes,
        categories=categories,
        names=names,
        name_category_map=name_category_map,
        theme_spans=theme_spans,
        subtheme_spans=subtheme_spans
    )

@app.route('/admin/update', methods=['POST'])
@login_required
def update_data():
    data = request.json
    with db.session.begin():
        if 'type' in data:
            if data['type'] == 'toggle':
                name_id = data['name_id']
                category_id = data['category_id']
                checked = data['checked']
                if checked:
                    db.session.execute(NameCategory.__table__.insert().values(name_id=name_id, category_id=category_id).prefix_with('IGNORE'))
                else:
                    db.session.execute(NameCategory.__table__.delete().where(NameCategory.name_id == name_id).where(NameCategory.category_id == category_id))
            elif data['type'] == 'add_theme':
                db.session.execute(Theme.__table__.insert().values(name=data['name']).prefix_with('IGNORE'))
            elif data['type'] == 'add_subtheme':
                db.session.execute(Subtheme.__table__.insert().values(theme_id=data['theme_id'], name=data['name']).prefix_with('IGNORE'))
            elif data['type'] == 'add_category':
                db.session.execute(Category.__table__.insert().values(subtheme_id=data['subtheme_id'], name=data['name']).prefix_with('IGNORE'))
            elif data['type'] == 'add_name':
                db.session.execute(Name.__table__.insert().values(name=data['name']).prefix_with('IGNORE'))
            elif data['type'] == 'delete_name':
                Name.query.filter_by(id=data['name_id']).delete()
    return jsonify({'status': 'success'})

@app.route('/_health')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)