from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import random
import logging
import os
from sqlalchemy import inspect
from tool_set_processor import populate_db_from_excel
from models import db, Theme, Subtheme, Category, Name, NameCategory

logging.basicConfig(level=logging.INFO)  # Add basic logging

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure key

# Import database configuration
from config import DATABASE_URL

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
    response_data = {'status': 'success'} # Prepare response data

    try:
        # Use db.session.begin() for the outer transaction management
        with db.session.begin(): 
            if 'type' in data:
                action_type = data.get('type')
                logging.info(f"Admin update action: {action_type} with data: {data}")

                if action_type == 'toggle':
                    name_id = data.get('name_id')
                    category_id = data.get('category_id')
                    checked = data.get('checked')

                    if name_id is None or category_id is None or checked is None:
                        raise ValueError("Missing data for toggle action")

                    assoc = db.session.query(NameCategory).filter_by(name_id=name_id, category_id=category_id).first()

                    if checked:
                        if not assoc:
                            new_assoc = NameCategory(name_id=name_id, category_id=category_id)
                            db.session.add(new_assoc)
                            logging.info(f"Added association: Name ID {name_id}, Category ID {category_id}")
                        else:
                            logging.info(f"Association already exists: Name ID {name_id}, Category ID {category_id}")
                    else:
                        if assoc:
                            db.session.delete(assoc)
                            logging.info(f"Deleted association: Name ID {name_id}, Category ID {category_id}")
                        else:
                            logging.info(f"Association not found for deletion: Name ID {name_id}, Category ID {category_id}")

                elif action_type == 'add_theme':
                    name = data.get('name', '').strip()
                    if not name: raise ValueError("Theme name cannot be empty")
                    existing = db.session.query(Theme).filter_by(name=name).first()
                    if not existing:
                        new_theme = Theme(name=name)
                        db.session.add(new_theme)
                        db.session.flush() # Flush to get ID if needed
                        response_data['new_id'] = new_theme.id
                        logging.info(f"Added Theme: {name} (ID: {new_theme.id})")
                    else:
                        response_data['status'] = 'ignored'
                        response_data['message'] = 'Theme already exists'
                        logging.info(f"Theme already exists: {name}")


                elif action_type == 'add_subtheme':
                    name = data.get('name', '').strip()
                    theme_id = data.get('theme_id')
                    if not name or theme_id is None: raise ValueError("Subtheme name or theme_id missing")
                    existing = db.session.query(Subtheme).filter_by(theme_id=theme_id, name=name).first()
                    if not existing:
                        new_subtheme = Subtheme(theme_id=theme_id, name=name)
                        db.session.add(new_subtheme)
                        db.session.flush()
                        response_data['new_id'] = new_subtheme.id
                        logging.info(f"Added Subtheme: {name} to Theme ID {theme_id} (ID: {new_subtheme.id})")
                    else:
                        response_data['status'] = 'ignored'
                        response_data['message'] = 'Subtheme already exists for this theme'
                        logging.info(f"Subtheme already exists: {name} for Theme ID {theme_id}")

                elif action_type == 'add_category':
                    name = data.get('name', '').strip()
                    subtheme_id = data.get('subtheme_id')
                    if not name or subtheme_id is None: raise ValueError("Category name or subtheme_id missing")
                    existing = db.session.query(Category).filter_by(subtheme_id=subtheme_id, name=name).first()
                    if not existing:
                        new_category = Category(subtheme_id=subtheme_id, name=name)
                        db.session.add(new_category)
                        db.session.flush()
                        response_data['new_id'] = new_category.id
                        logging.info(f"Added Category: {name} to Subtheme ID {subtheme_id} (ID: {new_category.id})")
                    else:
                        response_data['status'] = 'ignored'
                        response_data['message'] = 'Category already exists for this subtheme'
                        logging.info(f"Category already exists: {name} for Subtheme ID {subtheme_id}")

                elif action_type == 'add_name':
                    name = data.get('name', '').strip()
                    if not name: raise ValueError("Name cannot be empty")
                    existing = db.session.query(Name).filter_by(name=name).first()
                    if not existing:
                        new_name = Name(name=name)
                        db.session.add(new_name)
                        db.session.flush()
                        response_data['new_id'] = new_name.id
                        logging.info(f"Added Name: {name} (ID: {new_name.id})")
                    else:
                        response_data['status'] = 'ignored'
                        response_data['message'] = 'Name already exists'
                        logging.info(f"Name already exists: {name}")

                elif action_type == 'delete_name':
                    name_id = data.get('name_id')
                    if name_id is None: raise ValueError("Missing name_id for delete action")
                    
                    # 1. Delete associations first
                    db.session.query(NameCategory).filter_by(name_id=name_id).delete()
                    logging.info(f"Deleted associations for Name ID: {name_id}")

                    # 2. Delete the name itself
                    name_to_delete = db.session.query(Name).get(name_id)
                    if name_to_delete:
                        db.session.delete(name_to_delete)
                        logging.info(f"Deleted Name: {name_to_delete.name} (ID: {name_id})")
                    else:
                        logging.warning(f"Name ID {name_id} not found for deletion.")
                        response_data['status'] = 'ignored'
                        response_data['message'] = 'Name not found'
                
                else:
                     raise ValueError(f"Unknown action type: {action_type}")

        # The 'with db.session.begin():' block handles commit/rollback automatically
        logging.info("Admin update transaction completed successfully.")

    except ValueError as ve:
        # Rollback is handled automatically by exiting the 'with' block on error
        logging.error(f"Validation error during admin update: {ve}")
        response_data = {'status': 'error', 'message': str(ve)}
        return jsonify(response_data), 400 # Bad request
    except Exception as e:
        # Rollback is handled automatically by exiting the 'with' block on error
        logging.error(f"Error during admin update: {e}", exc_info=True)
        response_data = {'status': 'error', 'message': 'An internal error occurred.'}
        return jsonify(response_data), 500 # Internal server error

    return jsonify(response_data)

@app.route('/_health')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)