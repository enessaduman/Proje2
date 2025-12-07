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

#Safely reading and retrieving the JSON
try:
    with open('Recipes.json', 'r', encoding="utf-8") as f:
        raw_recipe_ing_data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    sys.exit(f"Critical Error: JSON file could not be read. {e}")

#Spliting the JSON Date according to dict block assigned type
recipes=[]
ingredients=[]
for block in raw_recipe_ing_data:
    if block.get('TYPE')=='MEAL':
        recipes.append(block)
    elif block.get('TYPE')=='INGREDIENT':
        ingredients.append(block)

recipe_raw_ing_lst = []

for recipe in recipes:
    recipe_ing_dict = {}
    raw_ingre_lst = []
    #Preventing 'Key' errors!
    IngredientsP = recipe.get('Ingredients Used', [])
    lemmatized_portions = [L.lemmatize(p.lower()) for p in IngredientsP]

    for ingredient in ingredients:
        #Type check - Casting
        ing_str = ingredient if isinstance(ingredient, str) else str(ingredient)
        for lemma_p in lemmatized_portions:
            if ing_str.lower() in lemma_p:
                raw_ingre_lst.append(ingredient)
                #we won't go through the other lemmatized_portions for already found element
                break

    if raw_ingre_lst:
        recipe_ing_dict['Food Name'] = recipe['Food Name']
        recipe_ing_dict['Raw Ingredients'] = raw_ingre_lst
        recipe_raw_ing_lst.append(recipe_ing_dict)
    else:
        print(f"Warning: No ingredients found for {recipe.get('Food Name', 'Unknown')}")
        sys.exit(1)  #Creating error code and exit
# ----------------------
#   DEFINING QUERIES
# -----------------------
#$parameter prevents the not SQL (since Falkor noSQL) but the Cypher injection attacks
# Query 1: Creating Recipe Nodes
CREATE_RECIPE_NODE = """
    UNWIND $r_data AS r
    MERGE (recipe:Recipe {name: r['Food Name'], instructions: r.Instructions})
    UNWIND r['Ingredients Used'] AS ingPortionSTR
    MERGE (i:IngredientP {ingPortion: ingPortionSTR})
    MERGE (recipe)-[:MADE_WITH]->(i)
"""
# Query 2: Linking Raw Ingredients
CREATE_RAW_INGREDIENT_NODE = """
    UNWIND $dict AS d
    MATCH (r:Recipe {name: d['Food Name']})
    UNWIND d['Raw Ingredients'] AS I
    MERGE (i:Ingredient {name: I})
    MERGE (r)-[:HAS_THE_ITEM]->(i)
"""
# Running the queries safely
try:
    graph.query(CREATE_RECIPE_NODE, {'r_data': recipes})
    graph.query(CREATE_RAW_INGREDIENT_NODE, {'dict': recipe_raw_ing_lst})
    print("Database update successful.")
except ResponseError as e:
    print(f"Cypher Query Execution Error: {e}")
except RedisConnectionError as e:
    print(f"Database Connection error while executing query: {e}")
