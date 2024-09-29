import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import re
import numpy as np
from collections import OrderedDict


def extract_json_from_prompt(prompt):
    # Regex to find the content between ```json and the closing ```
    json_match = re.search(r'```json\s*([\s\S]*?)```', prompt)

    if json_match:
        json_str = json_match.group(1)  # Extract the matched JSON part
        try:
            # Convert the extracted string into a JSON object
            json_data = json.loads(json_str)
            return json_data  # Returning as a Python dictionary
        except json.JSONDecodeError:
            print("Error: Unable to parse JSON.")
            return None
    else:
        print("Error: No JSON object found in the prompt.")
        return None


def load_json(json_path):
    try:
        # Specify encoding='utf-8' to handle non-ASCII characters
        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"File not found: {json_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {json_path}")
        return None


def field_prompt(user_prompt, field_rule, field_answer, client):
    field_rule = json.dumps(field_rule, indent=4, ensure_ascii=False)
    field_answer = json.dumps(field_answer, indent=4, ensure_ascii=False)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": (f"Użytkownik podał następującą wypowiedź: \n{user_prompt}\n Czy jesteś w stanie stwierdzić jaka powinna być wartość pola formularza podatkowego?"
                            f"Dla tego pola zdefiniowane są następujące reguły: \n{field_rule}\n. Zwróć odpwowiedź w postaci pliku .json takiego jak ten: {field_answer}"
                            f"Jeśli nie jesteś w stanie uzupełnić tego pola zostaw jego wartość niezmienioną i zwróć plik json oryginalny.")
            }
        ]
    )
    return completion.choices[0].message.content


def get_new_form_answers(user_prompt, rules_json, answers_json):
    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    new_answers = {'fields': []}

    rules_json_fields = rules_json.get('fields', [])
    answers_json_fields = answers_json.get('fields', [])

    for i in range(len(rules_json_fields)):

        prompt_text = field_prompt(user_prompt, rules_json_fields[i], answers_json_fields[i], client)
        json_field_answer = extract_json_from_prompt(prompt_text)

        if json_field_answer:
            new_answers['fields'].append(json_field_answer)
        else:
            new_answers['fields'].append(answers_json_fields[i])

    return new_answers


def get_empty_fields_id(current_answers):
    empty_ids = []
    for field in current_answers.get('fields', []):
        field_number = field.get('field_number')
        field_value = field.get('value')
        if field_value is None:
            if field_number is not None:
                empty_ids.append(field_number)
    return empty_ids


def prompt_chat(prompt):
    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return completion.choices[0].message.content


def generate_question(rules_id, rules_json_fields, current_answers, prompt_intro_to_sections, section):
    fields_to_ask_about = {'fields': []}
    for field in rules_json_fields.get('fields', []):
        field_number = field.get('field_number')
        if field_number in rules_id:
            fields_to_ask_about['fields'].append(field)

    prompt_to_question = (f"Tak wygląda dotychczasowe wypełnienie formularza: {current_answers}. "
                          f"Wygeneruj pytanie z prośbą o uzupełnienie informacji na temat {prompt_intro_to_sections[section]}. "
                          f"W którym znajdują się następujące pola: \n{json.dumps(fields_to_ask_about, indent=4, ensure_ascii=False)}\n"
                          "Nie generuj podpisu ani żadnych z tych rzeczy. Nie podawaj numerów pól a jedynie ich nazwy. Użytkownik nie widzi formularza.")

    return prompt_chat(prompt_to_question)


def generate_new_prompt(current_answers, rules_json_fields, prompt_intro_to_sections, sections_dict):
    empty_ids = get_empty_fields_id(current_answers)
    new_question = "Nothing to ask about"
    for section, ids in sections_dict.items():
        empty_rules_ids = np.intersect1d(ids, empty_ids)
        if len(empty_rules_ids) > 0:
            if section == "tax_calc":
                if 231 in empty_rules_ids:
                    empty_rules_ids = [231]
                elif len(empty_rules_ids) <= 8:
                    continue
            new_question = generate_question(empty_rules_ids, rules_json_fields, current_answers, prompt_intro_to_sections, section)
            break
    return new_question


sections_dict = OrderedDict(
    {'date_time_goal': [4, 5, 6],
     'id': [1, 7, 8, 9, 10],
     'address': [11, 12, 13, 14, 15, 16, 17, 18, 19],
     'subject_content': [20, 21, 22, 23],
     'tax_calc': [231, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33]
     }
)


prompt_intro_to_sections = OrderedDict(
    {'date_time_goal': "dokładnej daty wystąpienia czynności cywilno prawnej i/lub celu złożenia deklaracji",
     'id': "danych podatnika dokonującego zapłaty lub zwolnionego z podatku",
     'address': "adresu siedziby bądź obecnego zamieszkania osoby wypełniającej wniosek",
     'subject_content': "przedmiotu opodatkowania i treść czynności cywilnoprawnej",
     'tax_calc': "rodzaju zawartej umowy i związanej z tym stawki oraz informacji na temat podstawy do obliczenia podatku"
     }
)


script_dir = os.path.dirname(__file__)
json_form_rules_path = os.path.join(script_dir, '..', 'data', 'form_rules.json')
json_form_answers_path = os.path.join(script_dir, '..', 'data', 'form_anwsers.json')

user_prompt = ("Wczoraj kupiłem na giełdzie samochodowej Fiata 126p rok prod. 1975, kolor zielony. "
               "Przejechane ma 1000000 km, idzie jak przecinak, nic nie stuka, nic nie puka, dosłownie igła. "
               "Zapłaciłem za niego 1000zł ale jego wartość jest wyższa o 2000 zł i co mam z tym zrobić?")
rules_json = load_json(json_form_rules_path)
answers_json = load_json(json_form_answers_path)

# new_answers_json = get_new_form_answers(user_prompt, rules_json, answers_json)
# print(json.dumps(new_answers_json, indent=4, ensure_ascii=False))

print(generate_new_prompt(answers_json, rules_json, prompt_intro_to_sections, sections_dict))
