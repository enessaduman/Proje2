import argparse
from dataclasses import dataclass, asdict
import json
from typing import List, Dict, Any, Tuple


# --- 1. Dataclass Definition ---

@dataclass
class Recipe:
    """Dataclass holding basic information about a recipe."""
    name: str
    ingredients: List[str]  # All ingredients required for the recipe
    instructions: str


# --- 2. Simple Data Source (New and Updated List) ---

RECIPE_DATA = [
    Recipe(
        name="Egg Drop Soup",
        ingredients=["sesame oil", "water", "egg"],
        instructions="Boil water, beat the egg, and slowly pour into the boiling water, stirring. Add sesame oil."
    ),
    Recipe(
        name="Curry",
        ingredients=["olive oil", "beef", "curry powder"],
        instructions="Cook beef with olive oil and spices until browned. Add curry powder and simmer."
    ),
    Recipe(
        name="Minced Meat Pastry (Kıymalı Börek)",
        ingredients=["minced beef", "phyllo dough (yufka)"],
        instructions="Mix minced beef with spices and fill the phyllo dough sheets. Bake until golden."
    ),
    # Including recipes from the previous version to ensure the logic works:
    Recipe(
        name="Lentil Soup",
        ingredients=["red lentils", "water", "onion", "carrot", "mint", "salt", "oil"],
        instructions="Wash the lentils, boil them with other ingredients, blend them, and heat mint in oil."
    ),
    Recipe(
        name="Chicken Pilaf",
        ingredients=["rice", "chicken breast", "butter", "salt", "water", "black pepper"],
        instructions="Soak the rice. Boil and shred the chicken. Use chicken broth when cooking the rice and add the shredded chicken."
    ),
]


# --- 3. Application Logic (Flexible Matching and Interactive Filtering) ---

class RecipeRecommender:
    def __init__(self, data_source: List[Recipe], save_file: str = "saved_recipes.txt"):
        self.data_source = data_source
        self.save_file = save_file

    def get_ingredient_subtypes(self, keyword: str, all_ingredients: set) -> Dict[str, str]:
        """
        Finds all ingredient subtypes that match a keyword and returns them as a dictionary.
        """
        subtypes = {}
        for ing in all_ingredients:
            # If the user's input keyword is found inside the ingredient (flexible matching)
            if keyword.lower().strip() in ing:
                # Add it to the list of subtypes
                subtypes[ing] = ing
        return subtypes

    def interactive_filter(self, user_ingredients: List[str]) -> List[str]:
        """
        Analyzes user input and interactively asks for subtype selection if necessary.
        """
        all_ingredients = set()
        for recipe in self.data_source:
            for ing in recipe.ingredients:
                all_ingredients.add(ing.lower())

        final_ingredients = []

        for user_input in user_ingredients:
            matching_subtypes = self.get_ingredient_subtypes(user_input, all_ingredients)

            if len(matching_subtypes) > 1:
                # If there is more than one subtype, ask the user to select
                print(f"\n❓ The keyword '{user_input.upper()}' matches multiple ingredient types.")
                print("Please enter the number of the subtype you want to use:")

                # Prepare options
                options = list(matching_subtypes.keys())
                for i, option in enumerate(options, 1):
                    print(f"  [{i}] {option.capitalize()}")

                choice = -1
                while choice < 1 or choice > len(options):
                    try:
                        choice = int(input("Your selection (Enter Number): "))
                        if 1 <= choice <= len(options):
                            selected_ingredient = options[choice - 1]
                            print(f"✅ Selected: {selected_ingredient.capitalize()}")
                            final_ingredients.append(selected_ingredient)
                            break
                        else:
                            print("Invalid number. Please enter a number from the list.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")
            elif len(matching_subtypes) == 1:
                # If there is only one match, use it directly
                final_ingredients.append(list(matching_subtypes.keys())[0])
            else:
                # If no match, keep the original input (recipe-specific matching is still possible)
                final_ingredients.append(user_input)

        return final_ingredients

    def recommend_recipes(self, user_ingredients: List[str]) -> List[Dict[str, Any]]:
        """
        Ranks the best matching recipes based on the ingredients provided by the user.
        (The matching logic remains the same as the previous code.)
        """
        matching_recipes = []
        user_tokens = set()
        for ingredient in user_ingredients:
            user_tokens.update(ingredient.lower().strip().split())

        for recipe in self.data_source:
            recipe_ingredients_set = {m.lower().strip() for m in recipe.ingredients}

            common_count = 0
            matched_recipe_ingredients = set()

            for recipe_ingredient in recipe_ingredients_set:
                recipe_ingredient_tokens = set(recipe_ingredient.split())

                if not user_tokens.isdisjoint(recipe_ingredient_tokens):
                    if recipe_ingredient not in matched_recipe_ingredients:
                        common_count += 1
                        matched_recipe_ingredients.add(recipe_ingredient)

            if common_count > 0:
                missing_ingredients = recipe_ingredients_set.difference(matched_recipe_ingredients)
                match_ratio = common_count / len(recipe_ingredients_set)

                matching_recipes.append({
                    "recipe": recipe,
                    "common_count": common_count,
                    "match_ratio": match_ratio,
                    "missing_ingredients": missing_ingredients
                })

        sorted_recipes = sorted(
            matching_recipes,
            key=lambda x: (x['common_count'], x['match_ratio']),
            reverse=True
        )

        return sorted_recipes[:3]

    def save_recipes(self, recipes: List[Recipe]):
        # The saving logic remains the same
        try:
            with open(self.save_file, 'a', encoding='utf-8') as f:
                for recipe in recipes:
                    # Use ensure_ascii=False to correctly handle non-ASCII characters like in 'börek'
                    f.write(json.dumps(asdict(recipe), ensure_ascii=False) + "\n")
            print(f"\n✅ {len(recipes)} recommended recipe(s) successfully saved to '{self.save_file}'.")
        except IOError as e:
            print(f"\n❌ An error occurred during the saving process: {e}")


# --- 4. Argparse and Main Function ---

def main():
    parser = argparse.ArgumentParser(
        description="An application that recommends and saves the best matching food recipes based on available ingredients."
    )

    parser.add_argument(
        'ingredients',
        metavar='INGREDIENT',
        type=str,
        nargs='+',
        help='Enter the ingredients you have for recipe suggestion (e.g., oil beef water)'
    )

    args = parser.parse_args()
    user_ingredients = args.ingredients

    # Numeric validation remains the same
    invalid_inputs = []
    for item in user_ingredients:
        if any(char.isdigit() for char in item):
            invalid_inputs.append(item)

    if invalid_inputs:
        print("\n❌ Error: Ingredient names contain numeric characters (amounts or measurements).")
        print("Please enter only ingredient names. Invalid inputs: " + ', '.join(invalid_inputs))
        return

    print(f"\n👉 Initial Input: {', '.join(user_ingredients)}")

    recommender = RecipeRecommender(RECIPE_DATA)

    # New Step: Interactive Filtering
    filtered_ingredients = recommender.interactive_filter(user_ingredients)

    # If there are still ingredients left after filtering, continue
    if not filtered_ingredients:
        print("\n😔 No ingredients remaining after interactive filtering. Program terminated.")
        return

    print(f"\n👉 Filtered Ingredients: {', '.join(filtered_ingredients)}")

    # Recommend recipes (with Filtered ingredients)
    sorted_recommendations = recommender.recommend_recipes(filtered_ingredients)

    if sorted_recommendations:
        print("\n🌟 TOP MATCHING RECIPES Based on Your Ingredients: 🌟")

        recipes_to_save = []

        for i, item in enumerate(sorted_recommendations, 1):
            recipe = item['recipe']
            recipes_to_save.append(recipe)

            common_count = item['common_count']
            total_count = len(recipe.ingredients)
            match_percentage = int(item['match_ratio'] * 100)
            missing = ', '.join(item['missing_ingredients']) if item[
                'missing_ingredients'] else "*None (All Ingredients Present!)*"

            print(
                f"--- {i}. {recipe.name.upper()} ({match_percentage}% Match - {common_count}/{total_count} Ingredients Matched) ---")
            print(f"   MISSING INGREDIENTS: {missing}")
            print(f"   Instructions: {recipe.instructions[:50]}...")

        recommender.save_recipes(recipes_to_save)
    else:
        print("\n😔 Sorry, the ingredients you entered do not share any common ingredients with our recipes.")


if __name__ == "__main__":
    main()