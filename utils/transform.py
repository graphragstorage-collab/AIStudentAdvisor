import threading
import textwrap
from typing import List
from openai import OpenAI   # <-- switched to OpenAI

# Initialize OpenAI client
openai_client = OpenAI()    # <-- new client


RAG_TRANSFORM_PROMPT = """
You are transforming raw website text (copied directly via browser “Select All” or Playwright extraction) into a structured, clean, retrieval-friendly document for RAG.

Follow these rules:

1. Extract ALL meaningful information.
2. Clean up formatting issues caused by scraping (broken lines, duplicate headers, menus, footers unless useful).
3. Organize the content into clear sections with descriptive titles.
4. Rewrite lists, tables, link groups, and navigation text into readable document form.
5. If a URL is visible, include it as a proper link in that section.
6. If a link/button is shown but no URL appears in the scrape, note: "[Link/button present but URL not captured]".
7. Do NOT remove or summarize content that is instructional, procedural, deadline-related, or required for academic programs.
8. Summaries are ONLY for sections where summarization improves clarity without losing context.
9. Separate each section/chunk with the literal string:
###
10. DO NOT OMIT INFOMRATION. If there is a lot of content, keep it all, just organize it well.
11. Output ONLY the document. No explanations. No meta text. No commentary.

Here is an example:

    [WEBPAGE: fightingfor.nd.edu_stories_fighting-to-improve-hurricane-forecasts_

    Fighting to Improve Hurricane Forecasts

    Researchers at Notre Dame are working to enhance the accuracy of hurricane forecasts, which is crucial for timely evacuations and protecting residents. John Antapasis, the emergency management director for Tampa, recalls the challenges faced during Hurricane Andrew in 1992, where the uncertainty in storm predictions led to anxiety and poor preparedness. Today, advancements in technology have improved the specificity of forecasts, but predicting storm intensity at landfall remains a significant challenge.

    David Richter, a professor at Notre Dame, is focused on improving hurricane forecasting by making measurements in the storm's most extreme areas, particularly near the ocean surface. Traditional measurement methods are limited, often relying on data from high altitudes or satellites. Richter's research utilizes computational techniques to study turbulence and energy transfer in hurricanes, aiming to enhance predictive models.

    Richter's team collaborates with various institutions and employs Black Swift drones to gather data from within storms. These drones, launched from NOAA aircraft, collect critical information about wind speed and atmospheric flux near the ocean's surface. Additionally, specialized floats are deployed to map wave patterns during storms, allowing for simultaneous measurement of heat and moisture transfer between the ocean and atmosphere.

    __________________________________________________

    How Data Changes Evacuation Planning

    Understanding hurricanes is only the first step; the data collected by Richter's team has significant implications for emergency responders like John Antapasis. Accurate forecasting enables better decision-making regarding evacuations, resource allocation, and community preparedness. Antapasis emphasizes the importance of coordination among departments to respond effectively to emergencies, stating that improved data and technology can save lives.

    Joseph Cione, a lead meteorologist at NOAA, shares his experiences as a hurricane hunter and the need for enhanced observations to understand unusual storm behavior, as seen with Hurricane Helene. Cione stresses that the ultimate goal of their work is to protect property and save lives, and he believes that ongoing research will lead to better storm predictions.

    __________________________________________________

    Hurricane-Seasoned Experts

    Joseph Cione, a veteran hurricane hunter, reflects on the evolution of hurricane research over the past 30 years. He notes that while significant advancements have been made, there is still much to learn, particularly regarding unusual storm patterns. Cione's insights underline the importance of continuous research and the integration of emerging technologies to enhance storm understanding.

    As hurricane season progresses, Richter and his team remain prepared to deploy their drones and floats to gather data that could improve forecasting accuracy. Their work aims to provide critical information that can help communities better prepare for and respond to hurricanes.

    __________________________________________________]

Begin processing the input text now.
"""

def transform_raw_text(raw_text: str, llm_client=openai_client, model="gpt-4o-mini", max_tokens=2000) -> str:
    """
    Transforms raw scraped text into a clean, structured document suitable for RAG.
    """
    response = llm_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": RAG_TRANSFORM_PROMPT},
            {"role": "user", "content": raw_text}
        ],
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content
