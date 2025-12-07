import argparse
import sys
import os
from typing import List, Optional

# db_util modülünü import ediyoruz
try:
    import db_util
except ImportError:
    sys.exit("❌ Critical Error: 'db_util.py' module not found. Please ensure it is in the same directory.")


class InputValidator:
    """Handles validation and normalization of user inputs."""

    @staticmethod
    def validate_args(ingredients: List[str]) -> bool:
        if len(ingredients) > 5:
            print("⚠️  Warning: You entered more than 5 ingredients. Considering only the first 5.")
            del ingredients[5:]

        invalid_inputs = [item for item in ingredients if any(char.isdigit() for char in item)]
        if invalid_inputs:
            print(f"\n❌ Error: Ingredient names cannot contain numbers. Invalid inputs: {', '.join(invalid_inputs)}")
            return False
        return True


class IngredientResolver:
    """Checks DB. If exact match -> Keep. If fuzzy match -> List options and Abort."""

    def resolve_ingredients(self, raw_ingredients: List[str]) -> Optional[List[str]]:
        valid_ingredients = []
        ambiguity_flag = False

        print("\n🔍 Checking ingredients in the database...")

        for user_input in raw_ingredients:
            # ❌ ESKİ MANTIK (SİLİNECEK veya YORUMA ALINACAK):
            # if db_util.is_ingredient(user_input):
            #     print(f"   ✅ Found exact match: '{user_input}'")
            #     valid_ingredients.append(user_input)
            #     continue

            # ✅ YENİ MANTIK: Direkt Benzerlik Araması Yap
            print(f"   ⚠️  Scanning for matches or suggestions for '{user_input}'...")
            suggestions = db_util.find_similar_ingredients(user_input)

            if suggestions:
                # Durum 1: Birden fazla seçenek var (Örn: Milk, Oat Milk, Soy Milk)
                # VEYA tek seçenek var ama adı kullanıcının yazdığından farklı (typo düzeltmesi gibi)

                # Ancak senin istediğin tam olarak şu: 'milk' yazdım, içinde 'milk' geçen HEPSİNİ getir.
                # Eğer birden fazla sonuç varsa, Ambiguity (Belirsizlik) olarak işaretle ki kullanıcı görsün.
                if len(suggestions) > 1:
                    print(f"\n   🛑 Ambiguity detected for '{user_input}'. Did you mean one of these?")
                    print(f"      {'-' * 40}")
                    for s in suggestions:
                        print(f"      👉  {s}")  # s string olduğu için direkt yazdırıyoruz
                    print(f"      {'-' * 40}")
                    ambiguity_flag = True

                # Durum 2: Sadece TEK bir sonuç var.
                else:
                    suggestion = suggestions[0]
                    # Eğer tam eşleşme ise (milk == milk)
                    if suggestion.lower() == user_input.lower():
                        print(f"   ✅ Found exact match: '{suggestion}'")
                        valid_ingredients.append(suggestion)
                    else:
                        # Typo düzeltmesi olabilir (milkk -> Milk)
                        print(f"   ✅ Found single suggestion: '{suggestion}'. Automatically accepted.")
                        valid_ingredients.append(suggestion)

            else:
                print(f"   ❌ No similar ingredients found for '{user_input}'. Ignoring.")

        if ambiguity_flag:
            return None

        return valid_ingredients


class RecipeManager:
    """Handles fetching recipes and saving details."""

    def __init__(self, save_path: str = "Saved_Recipes.txt"):
        self.save_path = save_path

    def fetch_recommendations(self, ingredients: List[str]) -> List[dict]:
        if not ingredients:
            return []
        return db_util.list_recipies(ingredients)

    def save_recipe_details(self, recipe_name: str):
        details = db_util.recipe_details(recipe_name)
        if not details:
            print("❌ Error fetching recipe details.")
            return

        try:
            with open(self.save_path, 'a', encoding='utf-8') as f:
                f.write(f"\n{'=' * 40}\n")
                f.write(f"RECIPE: {details['Food Name'].upper()}\n")
                f.write(f"{'-' * 40}\n")
                f.write("INGREDIENTS:\n")
                for ing in details['Ingredients']:
                    f.write(f" - {ing}\n")
                f.write(f"\nINSTRUCTIONS:\n{details['Instructions']}\n")
                f.write(f"{'=' * 40}\n")

            abs_path = os.path.abspath(self.save_path)
            print(f"\n📄 Recipe saved successfully!\n📍 Path: {abs_path}")
        except IOError as e:
            print(f"❌ File I/O Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Recipe Recommender powered by FalkorDB."
    )
    # nargs='+' means at least one argument is required
    parser.add_argument(
        'ingredients',
        metavar='INGREDIENT',
        type=str,
        nargs='+',
        help='List of ingredients (Max 5 recommended)'
    )

    args = parser.parse_args()

    # 1. Validate Input
    if not InputValidator.validate_args(args.ingredients):
        return

    # 2. Resolve Ingredients (Strict Mode)
    resolver = IngredientResolver()
    final_ingredients = resolver.resolve_ingredients(args.ingredients)

    # Eğer None döndüyse, ambiguity var demektir.
    if final_ingredients is None:
        print("\n🚨 Execution Halted: Too many similar matches found.")
        print("💡 Please run the script again using the specific ingredient names listed above.")
        sys.exit(1)

    if not final_ingredients:
        print("\n😔 No valid ingredients identified to search for. Exiting.")
        return

    print(f"\n🚀 All ingredients validated! Searching recipes with: {', '.join(final_ingredients)}...")

    # 3. Fetch Recipes
    manager = RecipeManager()
    recipes = manager.fetch_recommendations(final_ingredients)

    if not recipes:
        print("\n🚫 No recipes found containing ALL these ingredients.")
        return

    # 4. Display Results
    print(f"\n🌟 Found {len(recipes)} Recipe(s):")
    for idx, rec in enumerate(recipes, 1):
        ing_preview = ", ".join(rec['Full Ingredients'])
        print(f"   {idx}. {rec['Food Name']} (Needs: {ing_preview[:50]}...)")

    # 5. User Selection for Saving (Interactive part kept only for final selection)
    while True:
        try:
            user_input = input("\n💾 Enter number to SAVE details (or '0' to exit): ")
            choice = int(user_input)

            if choice == 0:
                print("👋 Happy Cooking! Exiting.")
                break

            if 1 <= choice <= len(recipes):
                selected_recipe = recipes[choice - 1]
                manager.save_recipe_details(selected_recipe['Food Name'])
            else:
                print("⚠️ Invalid number. Choose from the list.")
        except ValueError:
            print("⚠️ Please enter a valid number.")


if __name__ == "__main__":
    main()