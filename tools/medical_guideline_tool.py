import requests
import xml.etree.ElementTree as ET
from backend.core.llm_provider import llm_provider
import re


class MedicalGuidelineTool:

    def __init__(self):
        self.llm = llm_provider.get_chat_llm()

    # -------------------------
    # Extract Medical Topic
    # -------------------------
    def extract_topic(self, question: str):

        prompt = f"""
Extract the main medical disease or health topic from the question.

Return ONLY the topic.

Question:
{question}
"""

        try:
            result = self.llm.invoke(prompt)
            return result.content.strip().lower()
        except:
            return question

    # -------------------------
    # MedlinePlus Search
    # -------------------------
    def search_medlineplus(self, topic: str):

        url = "https://wsearch.nlm.nih.gov/ws/query"

        params = {
            "db": "healthTopics",
            "term": topic,
            "retmax": 1
        }

        try:

            response = requests.get(url, params=params)

            if response.status_code != 200:
                return None

            root = ET.fromstring(response.text)

            document = root.find(".//document")

            if document is None:
                return None

            title = document.find("./content[@name='title']")
            summary = document.find("./content[@name='FullSummary']")
            article_url = document.attrib.get("url")

            # Clean HTML tags
            title_text = title.text if title is not None else None
            title_text = re.sub("<.*?>", "", title_text) if title_text else None

            summary_text = summary.text if summary is not None else None
            summary_text = re.sub("<.*?>", "", summary_text) if summary_text else None

            return {
                "title": title_text,
                "summary": summary_text[:500] if summary_text else None,
                "url": article_url
            }

        except Exception as e:
            print("MEDLINEPLUS ERROR:", e)
            return None

    # -------------------------
    # PubMed Search
    # -------------------------
    def search_pubmed(self, topic: str):

        try:

            search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

            params = {
                "db": "pubmed",
                "term": topic,
                "retmax": 1,
                "retmode": "json"
            }

            search_res = requests.get(search_url, params=params)

            if search_res.status_code != 200:
                return None

            id_list = search_res.json()["esearchresult"]["idlist"]

            if not id_list:
                return None

            article_id = id_list[0]

            summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

            params = {
                "db": "pubmed",
                "id": article_id,
                "retmode": "json"
            }

            summary_res = requests.get(summary_url, params=params)

            if summary_res.status_code != 200:
                return None

            result = summary_res.json()["result"][article_id]

            return {
                "title": result.get("title"),
                "journal": result.get("fulljournalname"),
                "pubdate": result.get("pubdate")
            }

        except Exception as e:
            print("PUBMED ERROR:", e)
            return None

    # -------------------------
    # Main Tool Function
    # -------------------------
    def search_medical_guidelines(self, question: str):

        topic = self.extract_topic(question)

        medline = self.search_medlineplus(topic)
        pubmed = self.search_pubmed(topic)

        print("\n======== TOOL DATA DEBUG ========")
        print("QUESTION:", question)
        print("TOPIC:", topic)
        print("MEDLINEPLUS:", medline)
        print("PUBMED:", pubmed)
        print("=================================\n")

        return {
            "topic": topic,
            "medlineplus": medline,
            "pubmed": pubmed
        }


medical_guideline_tool = MedicalGuidelineTool()