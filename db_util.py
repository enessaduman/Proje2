"""
This module provides utility functions to interact with the Recipe Graph Database.
It handles ingredient checks, finding similar ingredients, listing recipes,
and retrieving detailed recipe instructions using FalkorDB.
"""
from typing import List, Optional, Dict, Any
from falkordb import FalkorDB
from nltk.stem import WordNetLemmatizer

# Global instances
L = WordNetLemmatizer()
db = FalkorDB(host='localhost', port=6379)


def is_ingredient(temp_ingredient: str):
    """Checks if the given ingredient exists in the database."""
    graph = db.select_graph("RECIPIES")

    input_to_check = L.lemmatize(temp_ingredient.lower().capitalize())

    ingredient_search_query = """
        MATCH (i:Ingredient) 
        WHERE toLower(i.name) = toLower($temp_ingredient) 
        RETURN i
    """

    results = graph.query(ingredient_search_query, {'temp_ingredient': input_to_check})
    return len(results.result_set) > 0

def find_similar_ingredients(temp_ingredient: str):
    """
    Finds and returns a list of ingredients similar to the input string.
    Returns None if no matches are found.
    """
    graph = db.select_graph("RECIPIES")
    temp_ingredient = L.lemmatize(temp_ingredient.lower())

    retrieve_ingredient_query = """
        MATCH (i:Ingredient) 
        WHERE toLower(i.name) CONTAINS toLower($temp_ingredient)
        RETURN i.name
    """
    results = graph.query(retrieve_ingredient_query, {'temp_ingredient': temp_ingredient})

    if len(results.result_set) == 0:
        print(f"No similar ingredients found for '{temp_ingredient}'")
        return None
    # List comprehension for cleaner code
    ingredient_list=[]
    for record in results.result_set:
        ingredient_list.append(record[0])
    return ingredient_list


def list_recipies(input_ing_list: List[str]):
    """
    Returns a list of recipes that can be made with the given ingredients,
    including the required portion details for each recipe.
    """
    graph = db.select_graph("RECIPIES")

    search_recipe_query = """
        MATCH (rec:Recipe)-[:HAS_THE_ITEM]->(i:Ingredient)
        WHERE toLower(i.name) IN $input_ingredients
        WITH rec, COUNT(i) AS matchedCount, size($input_ingredients) AS requiredCount
        WHERE matchedCount = requiredCount
        MATCH (rec)-[:MADE_WITH]->(ingP:IngredientP)
        RETURN rec.name AS RecipeName, 
               collect(ingP.ingPortion) AS FullIngredientsList
    """
    lemmatized_input_list = [L.lemmatize(ing.lower()) for ing in input_ing_list]
    results = graph.query(search_recipe_query, {'input_ingredients': lemmatized_input_list})

    if len(results.result_set) == 0:
        return None
    recipe_list = [
        {
            'Food Name': result[0],
            'Full Ingredients': result[1]
        }
        for result in results.result_set
    ]
    return recipe_list


def recipe_details(recipe_name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves the full instructions and ingredient portions for a specific recipe.
    Case-insensitive*
    """
    graph = db.select_graph("RECIPIES")

    detailed_query = """
        MATCH (rec:Recipe)
        WHERE toLower(rec.name) = toLower($r_name)
        MATCH (rec)-[:MADE_WITH]->(ingP:IngredientP)
        RETURN rec.instructions AS Instructions, 
               collect(ingP.ingPortion) AS IngredientsPortion
    """

    results = graph.query(detailed_query, {'r_name': recipe_name.lower()})

    if len(results.result_set) == 0:
        return None

    result = results.result_set[0]
    return {
        'Food Name': result[0] if hasattr(result, '__getitem__') else recipe_name,  # Garantiye almak için
        'Instructions': result[0],
        'Ingredients': result[1]
    }
