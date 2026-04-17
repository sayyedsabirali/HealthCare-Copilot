import requests


class SymptomCheckerTool:

    BASE_URL = "https://clinicaltables.nlm.nih.gov/api/conditions/v3/search"

    def search_symptom(self, symptom: str):

        params = {
            "terms": symptom
        }

        response = requests.get(self.BASE_URL, params=params)

        if response.status_code != 200:
            return None

        data = response.json()

        if not data or len(data) < 4:
            return None

        conditions = data[3]

        return {
            "symptom": symptom,
            "possible_conditions": conditions[:5]
        }


symptom_checker_tool = SymptomCheckerTool()