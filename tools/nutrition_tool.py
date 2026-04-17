import requests
from backend.config.settings import settings


class NutritionTool:

    BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

    # Important nutrients only (LLM friendly)
    IMPORTANT_NUTRIENTS = [
        "Energy",
        "Carbohydrate, by difference",
        "Total Sugars",
        "Fiber, total dietary",
        "Protein",
        "Total lipid (fat)",
        "Sodium, Na",
        "Potassium, K",
        "Cholesterol"
    ]

    def get_food_nutrition(self, food: str):

        # Normalize food name
        food = food.lower().strip()

        if food.startswith("a "):
            food = food[2:]

        if food.endswith("s"):
            food = food[:-1]

        params = {
            "query": f"{food} raw",
            "api_key": settings.USDA_API_KEY,
            "pageSize": 5
        }

        try:

            response = requests.get(self.BASE_URL, params=params)

            if response.status_code != 200:
                print("USDA API ERROR:", response.text)
                return None

            data = response.json()

            foods = data.get("foods", [])

            if not foods:
                print("NO FOOD FOUND:", food)
                return None

            # Prefer raw food
            food_data = None

            for f in foods:
                description = f.get("description", "").lower()

                if "raw" in description:
                    food_data = f
                    break

            # fallback
            if not food_data:
                food_data = foods[0]

            nutrients = food_data.get("foodNutrients", [])

            nutrition = {
                "food_name": food_data.get("description"),
                "nutrients": {}
            }

            # Collect only important nutrients
            for n in nutrients:

                name = n.get("nutrientName")
                value = n.get("value")
                unit = n.get("unitName")

                if name in self.IMPORTANT_NUTRIENTS and value is not None:

                    nutrition["nutrients"][name] = {
                        "value": value,
                        "unit": unit
                    }
            return nutrition

        except Exception as e:

            print("NUTRITION TOOL ERROR:", e)

            return None


nutrition_tool = NutritionTool()