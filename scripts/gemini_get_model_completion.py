import os

from dotenv import load_dotenv
import google.generativeai as genai


def main():
    load_dotenv()
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content("Czym jest podatek od czynności cywilnoprawnych?")
    print(response.text)


if __name__ == "__main__":
    main()
