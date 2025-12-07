"""This Script basically receives the data
    that is scraped and stored in .json file,
    and designs a graphical database"""
import json
import sys
import nltk
from nltk.stem import WordNetLemmatizer
from falkordb import FalkorDB
#For specified errors and exceptions
from redis.exceptions import ConnectionError as RedisConnectionError, ResponseError
#Library Loading DONE!
#---------------------
#Calling tools from imported libs for lemmatizing strings and operating the db
nltk.download('wordnet')
L = WordNetLemmatizer()
try:
    db = FalkorDB(host='localhost', port=6379)
    graph = db.select_graph("RECIPIES")
except RedisConnectionError as e:
    sys.exit(f"Critical Error: Database connection failed. {e}")

# Safely reading and retrieving the JSON
try:
    with open('foods1.json', 'r', encoding="utf-8") as f:
        raw_recipe_ing_data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    sys.exit(f"Critical Error: JSON file could not be read. {e}")

# Spliting the JSON Date according to dict block assigned type
recipes = []
ingredients = []
for block in raw_recipe_ing_data:
    if block.get('TYPE') == 'MEAL':
        recipes.append(block)
    elif block.get('TYPE') == 'INGREDIENT':
        ingredients.append(block)

# ----------------------
# 1. Extracting raw ingredient name from portioned ones
# ----------------------
ingredient_names = set()
for block in ingredients:
    ing_name = block.get('Food_Name', '')
    if not ing_name or not isinstance(ing_name, str):
        continue

    cleaned_words = []
    for char in ing_name:
        if char.isalpha() or char.isspace():
            cleaned_words.append(char)
        else:
            cleaned_words.append(' ')

    cleaned_name_str = "".join(cleaned_words)
    for word in cleaned_name_str.split():
        lemmatized_word = L.lemmatize(word.lower())
        if len(lemmatized_word) > 1:
            ingredient_names.add(lemmatized_word)

# ----------------------
# 2. Matching and Comparing
# ----------------------
recipe_raw_ing_lst = []

for recipe in recipes:
    recipe_ing_dict = {}
    IngredientsP = recipe.get('Ingredients_Used', [])
    portion_words = set()

    for portion_str in IngredientsP:
        if not portion_str or not isinstance(portion_str, str):
            continue

        cleaned_chars = []
        for char in portion_str:
            if char.isalpha() or char.isspace():
                cleaned_chars.append(char)
            else:
                cleaned_chars.append(' ')

        cleaned_portion = "".join(cleaned_chars)
        for word in cleaned_portion.split():
            lemmatized_word = L.lemmatize(word.lower())
            if len(lemmatized_word) > 1:
                portion_words.add(lemmatized_word)

    found_ingredient_keywords = ingredient_names.intersection(portion_words)

    if found_ingredient_keywords:
        recipe_ing_dict['Food_Name'] = recipe['Food_Name']
        recipe_ing_dict['Raw_Ingredients'] = list(found_ingredient_keywords)
        recipe_raw_ing_lst.append(recipe_ing_dict)
    else:
        print(f"Warning: No ingredients found for {recipe.get('Food_Name', 'Unknown')}")
        # sys.exit(1)
# ----------------------
#   DEFINING QUERIES
# -----------------------
# $parameter prevents the not SQL (since Falkor noSQL) but the Cypher injection attacks
# Query 1: Creating Recipe Nodes
CREATE_RECIPE_NODE = """
    UNWIND $r_data AS r
    MERGE (recipe:Recipe {name: r.Food_Name, instructions: r.Instructions})
    WITH recipe,r
    UNWIND r.Ingredients_Used AS ingPortionSTR
    MERGE (i:IngredientP {ingPortion: ingPortionSTR})
    MERGE (recipe)-[:MADE_WITH]->(i)
"""
# Query 2: Linking Raw Ingredients
CREATE_RAW_INGREDIENT_NODE = """
    UNWIND $dict AS d
    MATCH (r:Recipe {name: d.Food_Name})
    WITH r,d
    UNWIND d.Raw_Ingredients AS I
    MERGE (i:Ingredient {name: I})
    MERGE (r)-[:HAS_THE_ITEM]->(i)
"""
print("Starting database update...")

# Running the queries safely
try:
    graph.query(CREATE_RECIPE_NODE, {'r_data': recipes})
    graph.query(CREATE_RAW_INGREDIENT_NODE, {'dict': recipe_raw_ing_lst})
    print("Database update successful.")
except ResponseError as e:
    print(f"Cypher Query Execution Error: {e}")
except RedisConnectionError as e:
    print(f"Database Connection error while executing query: {e}")
