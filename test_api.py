import requests
import json

base_url = 'http://localhost:5001'

# Test /api/subthemes endpoint
def test_subthemes():
    print("\n--- Testing /api/subthemes ---")
    # Get a theme ID first from the database
    try:
        from app import Theme, db, app
        with app.app_context():
            first_theme = Theme.query.first()
            theme_id = first_theme.id if first_theme else None
            if theme_id is None:
                print("No themes found in database")
                return
            print(f"Using theme ID: {theme_id}")
        
        response = requests.get(f'{base_url}/api/subthemes', params={'theme_id': theme_id})
        print(f"Status code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error testing subthemes: {e}")

# Test /api/categories endpoint
def test_categories():
    print("\n--- Testing /api/categories ---")
    # Get a subtheme ID first from the database
    try:
        from app import Subtheme, db, app
        with app.app_context():
            first_subtheme = Subtheme.query.first()
            subtheme_id = first_subtheme.id if first_subtheme else None
            if subtheme_id is None:
                print("No subthemes found in database")
                return
            print(f"Using subtheme ID: {subtheme_id}")
        
        response = requests.get(f'{base_url}/api/categories', params={'subtheme_id': subtheme_id})
        print(f"Status code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error testing categories: {e}")

# Test /api/random_name endpoint
def test_random_name():
    print("\n--- Testing /api/random_name ---")
    # Get a category ID first from the database
    try:
        from app import Category, db, app
        with app.app_context():
            first_category = Category.query.first()
            category_id = first_category.id if first_category else None
            if category_id is None:
                print("No categories found in database")
                return
            print(f"Using category ID: {category_id}")
        
        response = requests.get(f'{base_url}/api/random_name', params={'category_id': category_id})
        print(f"Status code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error testing random name: {e}")

if __name__ == "__main__":
    print("Testing API endpoints...")
    test_subthemes()
    test_categories()
    test_random_name()
    print("\nAPI tests completed")
