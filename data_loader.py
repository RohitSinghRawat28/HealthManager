import h5py
import numpy as np
import json
import os
import logging
from app import db
from models import Recipe, FoodCategory

class DataLoader:
    def __init__(self):
        self.categories_file = 'data/food_categories.json'
        self.recipes_file = 'data/sample_recipes.json'
    
    def load_food_categories(self):
        """Load Food-101 categories into database"""
        try:
            with open(self.categories_file, 'r') as f:
                categories_data = json.load(f)
            
            for category_id, category_name in categories_data.items():
                existing_category = FoodCategory.query.filter_by(category_id=int(category_id)).first()
                if not existing_category:
                    category = FoodCategory(
                        category_id=int(category_id),
                        name=category_name,
                        description=f"Recipes for {category_name}"
                    )
                    db.session.add(category)
            
            db.session.commit()
            logging.info(f"Loaded {len(categories_data)} food categories")
            return True
            
        except Exception as e:
            logging.error(f"Error loading food categories: {e}")
            return False
    
    def load_sample_recipes(self):
        """Load sample recipes into database"""
        try:
            with open(self.recipes_file, 'r') as f:
                recipes_data = json.load(f)
            
            for recipe_data in recipes_data:
                existing_recipe = Recipe.query.filter_by(name=recipe_data['name']).first()
                if not existing_recipe:
                    recipe = Recipe(
                        name=recipe_data['name'],
                        description=recipe_data.get('description', ''),
                        ingredients=json.dumps(recipe_data.get('ingredients', [])),
                        instructions=recipe_data.get('instructions', ''),
                        prep_time=recipe_data.get('prep_time', 0),
                        cook_time=recipe_data.get('cook_time', 0),
                        servings=recipe_data.get('servings', 1),
                        calories_per_serving=recipe_data.get('calories_per_serving', 0),
                        protein=recipe_data.get('protein', 0),
                        carbs=recipe_data.get('carbs', 0),
                        fat=recipe_data.get('fat', 0),
                        fiber=recipe_data.get('fiber', 0),
                        sugar=recipe_data.get('sugar', 0),
                        sodium=recipe_data.get('sodium', 0),
                        category=recipe_data.get('category', 'Unknown'),
                        tags=json.dumps(recipe_data.get('tags', [])),
                        food_category_id=recipe_data.get('food_category_id')
                    )
                    db.session.add(recipe)
            
            db.session.commit()
            logging.info(f"Loaded {len(recipes_data)} sample recipes")
            return True
            
        except Exception as e:
            logging.error(f"Error loading sample recipes: {e}")
            return False
    
    def inspect_h5_dataset(self, dataset_path):
        """Inspect HDF5 dataset structure"""
        try:
            with h5py.File(dataset_path, 'r') as f:
                print("Dataset structure:")
                def print_structure(name, obj):
                    print(f"  {name}: {obj}")
                    if hasattr(obj, 'shape'):
                        print(f"    Shape: {obj.shape}")
                    if hasattr(obj, 'dtype'):
                        print(f"    Type: {obj.dtype}")
                
                f.visititems(print_structure)
                
                # Try to load sample data
                if 'images' in f:
                    images = f['images']
                    print(f"\nImages shape: {images.shape}")
                    print(f"Images dtype: {images.dtype}")
                    print(f"Sample pixel values: {images[0][0][0]}")
                
                if 'category' in f:
                    labels = f['category']
                    print(f"\nLabels shape: {labels.shape}")
                    print(f"Labels dtype: {labels.dtype}")
                    print(f"Unique categories: {len(np.unique(labels[:]))}")
                    print(f"Sample labels: {labels[:10]}")
                
        except Exception as e:
            logging.error(f"Error inspecting dataset: {e}")
    
    def extract_sample_images(self, dataset_path, output_dir='static/sample_images', num_samples=10):
        """Extract sample images for visualization"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            with h5py.File(dataset_path, 'r') as f:
                images = f['images']
                labels = f['category']
                
                # Get random sample indices
                indices = np.random.choice(len(images), num_samples, replace=False)
                
                for i, idx in enumerate(indices):
                    img_array = images[idx]
                    label = labels[idx]
                    
                    # Convert to PIL Image and save
                    from PIL import Image
                    img = Image.fromarray((img_array.squeeze() * 255).astype(np.uint8), mode='L')
                    filename = f"sample_{i}_category_{label}.png"
                    img.save(os.path.join(output_dir, filename))
                
                logging.info(f"Extracted {num_samples} sample images to {output_dir}")
                
        except Exception as e:
            logging.error(f"Error extracting sample images: {e}")

def initialize_data():
    """Initialize all data on app startup"""
    loader = DataLoader()
    
    # Load food categories
    loader.load_food_categories()
    
    # Load sample recipes
    loader.load_sample_recipes()
    
    # Inspect dataset if available
    dataset_path = os.environ.get('FOOD101_DATASET_PATH', 'data/food_c101_n10099_r32x32x1.h5')
    if os.path.exists(dataset_path):
        logging.info("Found Food-101 dataset")
        # loader.inspect_h5_dataset(dataset_path)
        # loader.extract_sample_images(dataset_path)
    else:
        logging.warning("Food-101 dataset not found. Place the .h5 file in the data directory.")
