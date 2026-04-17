import requests


class DrugInteractionTool:

    BASE_URL = "https://api.fda.gov/drug/label.json"

    def get_drug_info(self, drug_name: str):

        params = {
            "search": f'openfda.brand_name:"{drug_name}" OR openfda.generic_name:"{drug_name}"',
            "limit": 1
        }

        try:

            response = requests.get(self.BASE_URL, params=params)

            print("FDA SEARCH:", drug_name)
            print("STATUS:", response.status_code)

            if response.status_code != 200:
                return None

            data = response.json()
            results = data.get("results", [])

            if not results:
                return None

            drug_data = results[0]

            return {
                "drug_name": drug_name,
                "indications": drug_data.get("indications_and_usage", []),
                "warnings": drug_data.get("warnings", []),
                "interactions": drug_data.get("drug_interactions", [])
            }

        except Exception as e:

            print("FDA ERROR:", e)
            return None


    def check_interaction(self, drugs: list):

        drug_infos = []

        for drug in drugs:

            drug = drug.strip().lower()

            info = self.get_drug_info(drug)

            if info:
                drug_infos.append(info)

        return drug_infos


drug_interaction_tool = DrugInteractionTool()