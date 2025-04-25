from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import random

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure key

# Import database configuration
from config import DATABASE_URL

# Configure SQLAlchemy with the appropriate database URL
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Automatically create all tables on startup (avoids needing the shell)
with app.app_context():
    db.create_all()

# We'll import and initialize the Dash app after creating the Flask app
from dashboard import get_dash_app
dash_app = get_dash_app()
dash_app.init_app(app)  # Initialize the Dash app with our Flask app

# Models
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
    names = db.relationship('Name', secondary='name_categories')

class Name(db.Model):
    __tablename__ = 'names'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    categories = db.relationship('Category', secondary='name_categories')

class NameCategory(db.Model):
    __tablename__ = 'name_categories'
    name_id = db.Column(db.Integer, db.ForeignKey('names.id'), primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), primary_key=True)

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
    themes = Theme.query.all()
    return render_template('index.html', themes=themes)

@app.route('/api/subthemes')
def get_subthemes():
    theme_id = request.args.get('theme_id')
    try:
        theme_id = int(theme_id)
    except (TypeError, ValueError):
        return jsonify([])
    subthemes = Subtheme.query.filter_by(theme_id=theme_id).all()
    # Return descriptive subtheme names combining theme and subtheme to avoid duplicates
    response = jsonify([
        {'id': s.id, 'name': f"{s.theme.name} - {s.name}"}
        for s in subthemes
    ])
    # Ensure no CORS or authentication issues
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
    # Return descriptive category names combining theme, subtheme, and category
    response = jsonify([
        {'id': c.id, 'name': f"{c.subtheme.theme.name} - {c.subtheme.name} - {c.name}"}
        for c in categories
    ])
    # Ensure no CORS or authentication issues
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
    # Ensure no CORS or authentication issues
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
    # Fetch all data needed for the admin table
    themes = Theme.query.order_by(Theme.name).all()
    subthemes = Subtheme.query.join(Theme).order_by(Theme.name, Subtheme.name).all()
    categories = Category.query.join(Category.subtheme).join(Subtheme.theme).order_by(Theme.name, Subtheme.name, Category.name).all()
    names = Name.query.order_by(Name.name).all()

    # Create a dictionary to easily check Name-Category associations
    name_category_map = {}
    associations = NameCategory.query.all()
    for assoc in associations:
        if assoc.name_id not in name_category_map:
            name_category_map[assoc.name_id] = set()
        name_category_map[assoc.name_id].add(assoc.category_id)

    # Compute theme_spans and subtheme_spans for table headers
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)  # Allow external connections