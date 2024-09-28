import os
from dotenv import load_dotenv
from openai import OpenAI


def main():
    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": "Czym jest podatek od czynności cywilnoprawnych?"
            }
        ]
    )

    print(completion.choices[0].message.content)


if __name__ == "__main__":
    main()
