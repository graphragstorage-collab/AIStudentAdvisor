import base64
import itertools
import os
from cerebras.cloud.sdk import Cerebras

API_KEYS = [
    "csk-tn98d46prf8mvhwvyy8d5y48ncck2w2xc6336y9dxvcd4eyt",
    "csk-f43h2hjymmty4489n22n5966ty6336fvw59m4m4d8rr499xt",
]

MODEL = "gpt-oss-140b"  # ⚠️ must support vision
MAX_TOKENS = 4096
TEMPERATURE = 0.3

clients = [Cerebras(api_key=k) for k in API_KEYS]
client_cycle = itertools.cycle(clients)

def load_image_base64(path: str) -> str:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Image not found: {path}")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def chat_loop_with_image():
    print("🖼️  Cerebras Image Chat")
    print("-" * 50)

    image_path = input("Enter image path: ").strip()
    image_b64 = load_image_base64(image_path)

    chat_history = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": image_b64,  # ✅ STRING, not dict
                }
            ],
        }
    ]

    print("✅ Image loaded. Ask questions about it.")
    print("Type 'exit' to quit.")

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in {"exit", "quit"}:
                break

            chat_history.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_input,
                        }
                    ],
                }
            )

            client = next(client_cycle)

            response = client.chat.completions.create(
                model=MODEL,
                messages=chat_history,
                max_completion_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                top_p=1,
            )

            assistant_text = response.choices[0].message.content
            print("\nAssistant:")
            print(assistant_text)

            chat_history.append(
                {
                    "role": "assistant",
                    "content": assistant_text,
                }
            )

        except Exception as e:
            print("\n⚠️ ERROR")
            print(type(e).__name__, e)

if __name__ == "__main__":
    chat_loop_with_image()

