import json
from collections import defaultdict
from app import db
from models import Recipe
import logging

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.recipe_ids = set()

class Trie:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word, recipe_id):
        """Insert a word into the trie with associated recipe ID"""
        node = self.root
        word = word.lower().strip()
        
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            node.recipe_ids.add(recipe_id)
        
        node.is_end = True
    
    def search(self, prefix):
        """Search for all recipe IDs that match the prefix"""
        node = self.root
        prefix = prefix.lower().strip()
        
        for char in prefix:
            if char not in node.children:
                return set()
            node = node.children[char]
        
        return node.recipe_ids
    
    def search_partial(self, word):
        """Search for partial matches"""
        word = word.lower().strip()
        all_matches = set()
        
        # Search for the word as a prefix
        exact_matches = self.search(word)
        all_matches.update(exact_matches)
        
        # Search for the word as a substring
        for i in range(len(word)):
            prefix_matches = self.search(word[i:])
            all_matches.update(prefix_matches)
        
        return all_matches

class RecipeSearchEngine:
    def __init__(self):
        self.name_trie = Trie()
        self.ingredient_trie = Trie()
        self.tag_trie = Trie()
        self.category_index = defaultdict(set)
        self.is_initialized = False
        
        # Initialize the search engine
        self.build_indices()
    
    def build_indices(self):
        """Build search indices from recipes in database"""
        try:
            recipes = Recipe.query.all()
            
            for recipe in recipes:
                # Index recipe name
                if recipe.name:
                    words = recipe.name.split()
                    for word in words:
                        self.name_trie.insert(word, recipe.id)
                
                # Index ingredients
                if recipe.ingredients:
                    try:
                        ingredients = json.loads(recipe.ingredients)
                        for ingredient in ingredients:
                            if isinstance(ingredient, str):
                                words = ingredient.split()
                                for word in words:
                                    self.ingredient_trie.insert(word, recipe.id)
                            elif isinstance(ingredient, dict) and 'name' in ingredient:
                                words = ingredient['name'].split()
                                for word in words:
                                    self.ingredient_trie.insert(word, recipe.id)
                    except (json.JSONDecodeError, TypeError):
                        # Handle cases where ingredients is not valid JSON
                        words = recipe.ingredients.split()
                        for word in words:
                            if word.strip():
                                self.ingredient_trie.insert(word, recipe.id)
                
                # Index tags
                if recipe.tags:
                    try:
                        tags = json.loads(recipe.tags)
                        for tag in tags:
                            self.tag_trie.insert(tag, recipe.id)
                    except (json.JSONDecodeError, TypeError):
                        # Handle cases where tags is not valid JSON
                        tags = recipe.tags.split(',')
                        for tag in tags:
                            if tag.strip():
                                self.tag_trie.insert(tag.strip(), recipe.id)
                
                # Index category
                if recipe.category:
                    self.category_index[recipe.category.lower()].add(recipe.id)
            
            self.is_initialized = True
            logging.info(f"Search indices built for {len(recipes)} recipes")
            
        except Exception as e:
            logging.error(f"Error building search indices: {e}")
    
    def search_recipes(self, query, limit=20):
        """Search recipes using multiple criteria"""
        if not self.is_initialized:
            self.build_indices()
        
        query = query.strip()
        if not query:
            return []
        
        # Collect recipe IDs from different search methods
        recipe_ids = set()
        
        # Search in recipe names
        name_matches = self.name_trie.search_partial(query)
        recipe_ids.update(name_matches)
        
        # Search in ingredients
        ingredient_matches = self.ingredient_trie.search_partial(query)
        recipe_ids.update(ingredient_matches)
        
        # Search in tags
        tag_matches = self.tag_trie.search_partial(query)
        recipe_ids.update(tag_matches)
        
        # Search in categories
        for category, ids in self.category_index.items():
            if query.lower() in category:
                recipe_ids.update(ids)
        
        # Search for multiple words
        words = query.split()
        if len(words) > 1:
            for word in words:
                if len(word) >= 2:  # Only search words with 2+ characters
                    name_matches = self.name_trie.search_partial(word)
                    recipe_ids.update(name_matches)
                    
                    ingredient_matches = self.ingredient_trie.search_partial(word)
                    recipe_ids.update(ingredient_matches)
                    
                    tag_matches = self.tag_trie.search_partial(word)
                    recipe_ids.update(tag_matches)
        
        # Get recipes from database
        if recipe_ids:
            recipes = Recipe.query.filter(Recipe.id.in_(recipe_ids)).limit(limit).all()
            
            # Sort by relevance (simple approach - could be improved)
            def relevance_score(recipe):
                score = 0
                query_lower = query.lower()
                
                # Higher score for exact name matches
                if recipe.name and query_lower in recipe.name.lower():
                    score += 10
                
                # Medium score for ingredient matches
                if recipe.ingredients:
                    try:
                        ingredients = json.loads(recipe.ingredients)
                        for ingredient in ingredients:
                            ingredient_text = str(ingredient).lower()
                            if query_lower in ingredient_text:
                                score += 5
                    except:
                        if query_lower in recipe.ingredients.lower():
                            score += 5
                
                # Lower score for tag matches
                if recipe.tags:
                    try:
                        tags = json.loads(recipe.tags)
                        for tag in tags:
                            if query_lower in str(tag).lower():
                                score += 3
                    except:
                        if query_lower in recipe.tags.lower():
                            score += 3
                
                # Category matches
                if recipe.category and query_lower in recipe.category.lower():
                    score += 7
                
                return score
            
            recipes.sort(key=relevance_score, reverse=True)
            return recipes
        
        return []
    
    def search_by_ingredients(self, ingredients_list, limit=20):
        """Search recipes that contain any of the specified ingredients"""
        if not self.is_initialized:
            self.build_indices()
        
        recipe_ids = set()
        
        for ingredient in ingredients_list:
            ingredient = ingredient.strip()
            if ingredient:
                matches = self.ingredient_trie.search_partial(ingredient)
                recipe_ids.update(matches)
        
        if recipe_ids:
            recipes = Recipe.query.filter(Recipe.id.in_(recipe_ids)).limit(limit).all()
            return recipes
        
        return []
    
    def search_by_category(self, category, limit=20):
        """Search recipes by category"""
        if not self.is_initialized:
            self.build_indices()
        
        category_lower = category.lower()
        recipe_ids = set()
        
        # Exact category match
        if category_lower in self.category_index:
            recipe_ids.update(self.category_index[category_lower])
        
        # Partial category match
        for cat, ids in self.category_index.items():
            if category_lower in cat:
                recipe_ids.update(ids)
        
        if recipe_ids:
            recipes = Recipe.query.filter(Recipe.id.in_(recipe_ids)).limit(limit).all()
            return recipes
        
        return []
    
    def get_popular_recipes(self, limit=20):
        """Get popular recipes (simple implementation - could use view counts, ratings, etc.)"""
        return Recipe.query.order_by(Recipe.id.desc()).limit(limit).all()
    
    def get_recipes_by_nutrition(self, max_calories=None, min_protein=None, limit=20):
        """Search recipes by nutritional criteria"""
        query = Recipe.query
        
        if max_calories:
            query = query.filter(Recipe.calories_per_serving <= max_calories)
        
        if min_protein:
            query = query.filter(Recipe.protein >= min_protein)
        
        return query.limit(limit).all()
    
    def refresh_indices(self):
        """Refresh search indices (call after adding new recipes)"""
        self.__init__()
