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

    # Clean and standardized input
    temp_ingredient = L.lemmatize(temp_ingredient.lower().capitalize())

    ingredient_search_query = "MATCH (i:Ingredient {name: $temp_ingredient}) RETURN i"

    results = graph.query(ingredient_search_query, {'temp_ingredient': temp_ingredient})
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
        WHERE i.name =~ '(?i).*' + $temp_ingredient + '.*'
        RETURN i.name AS ingredient_name
    """
    results = graph.query(retrieve_ingredient_query, {'temp_ingredient': temp_ingredient})

    if len(results.result_set) == 0:
        print(f"No similar ingredients found for '{temp_ingredient}'")
        return None
    # List comprehension for cleaner code
    return [record['ingredient_name'] for record in results.result_set]

def list_recipies(input_ing_list: List[str]):
    """
    Returns a list of recipes that can be made with the given ingredients,
    including the required portion details for each recipe.
    """
    graph = db.select_graph("RECIPIES")

    search_recipe_query = """
        MATCH (rec:Recipe)
        WHERE ALL(ingName IN $input_ingredients 
                  WHERE EXISTS((rec)-[:HAS_THE_ITEM]->(:Ingredient {name: ingName})))
        MATCH (rec)-[:MADE_WITH]->(ingP:IngredientP)
        RETURN rec.name AS RecipeName, 
               collect(ingP.ingPortion) AS FullIngredientsList
    """

    # List comprehension for processing input list
    lemmatized_input_list = [L.lemmatize(ing.lower().capitalize()) for ing in input_ing_list]
    results = graph.query(search_recipe_query, {'input_ingredients': lemmatized_input_list})

    if len(results.result_set) == 0:
        return None
    recipe_list = [
        {
            'Food Name': result['RecipeName'],
            'Full Ingredients': result['FullIngredientsList']
        }
        for result in results.result_set
    ]
    return recipe_list

def recipe_details(recipe_name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves the full instructions and ingredient portions for a specific recipe.
    """
    graph = db.select_graph("RECIPIES")
    standardized_name = recipe_name.lower().capitalize()

    detailed_query = """
        MATCH (rec:Recipe {name: $r_name})
        MATCH (rec)-[:MADE_WITH]->(ingP:IngredientP)
        RETURN rec.instructions AS Instructions, 
               collect(ingP.ingPortion) AS IngredientsPortion
    """
    results = graph.query(detailed_query, {'r_name': standardized_name})

    if len(results.result_set) == 0:
        return None

    result = results.result_set[0]
    return {
        'Food Name': recipe_name,
        'Instructions': result['Instructions'],
        'Ingredients': result['IngredientsPortion']
    }
