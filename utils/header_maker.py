import threading
import textwrap
from typing import List
from openai import OpenAI   # <-- switched to OpenAI
from cerebras.cloud.sdk import Cerebras

# Initialize OpenAI client
api_keys = [
    "csk-tn98d46prf8mvhwvyy8d5y48ncck2w2xc6336y9dxvcd4eyt",
    "csk-f43h2hjymmty4489n22n5966ty6336fvw59m4m4d8rr499xt",
    "csk-d8wcjrn639wftfcp8858yr9wtvrw8y5dm4mkfcp52xh6rnem",
    "csk-twcjfk4mwmtm3hnkd6pn6n282whrvte88c9pcrct69tw38m6",
    "csk-mppyvph8kxx9n6dxxcmhrnxjwkveyxjfrrm23eyyyxfjmfy4",
    "csk-n9r5k3h62pcjwn5393k4wct8y65enw6pkypmwwrj4cm8j23n",
    "csk-2j548nk43nw2ftr6368yxekdtp6rfw355c45832etttc8522",
    "csk-tpwdj98pewtepj4c5v3d8eejnx8t3rrdj8yh54f2vd8vprk6",
    "csk-mknjvx8xxpm2v4nryhe6v963cwxekdmm3dd8ftydtvjhnyn8",
    "csk-5ht9eh59wd289pycrk9vvfdcffxxrpmyjx9e29hyk3jfjjcx",
    "csk-fvj93vywv283cmt69mvyhmywyymrpd2fndhm9x3djmh8mc2h",
    "csk-m49vrdt4mfc5n3mxk4496wddevdrrx39erxyf3d3cv58jytm",
    "csk-839ek535y939jcjm6fynj8nd3cj369xpcet2rfdtrv9xpxw6",
    "csk-ccevmrkdpdhjn23c3crmmye8tejj6vpy5jf8dcrvthe53y8r",
    "csk-xyv3j8wej9mxtnf32mvrxtxrwt3wt3nj8jm68h5r8cvkxn63",

]

openai_client = OpenAI()    # <-- new client


llm_clients = []
for key in api_keys:
    llm_client = Cerebras(api_key=key)
    llm_clients.append(llm_client)

def create_header(text: str, llm_client=llm_client, model="gpt-4o-mini", max_tokens=15000):
    prompt = f"""
        You are getting a chunk of text from the beginning of a website. 
        You must create a header that can go above every chunk so that it is easily identifable as to what the general website main idea of the website is.
        Make sure that the header isn't longer than roughly 500 words.
        You should remain as factual as possible, leaving any opinions about the text out.
        Refrain from using any personal pronouns like "I" or "We"
        Include useful key words in the header (like class names or organization names). Make sure documents for a class (CS180 for example) have that class in the header.
        The following is the first chunk from the website:
        {text}
        """
    passing = False
    while not passing:
        try:
            completion = llm_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b",
                max_completion_tokens=max_tokens,
                temperature=0.3,   # Deterministic routing
                top_p=1,
                stream=False
            )
            passing = True
        except Exception as e:
            print(e)

    answer = completion.choices[0].message.content.strip()

    return answer
