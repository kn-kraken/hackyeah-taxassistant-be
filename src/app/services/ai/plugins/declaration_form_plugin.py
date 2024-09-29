import asyncio
import json
import logging
import os

from openai import AsyncOpenAI
from pydantic import BaseModel
from semantic_kernel.functions import kernel_function

from app.services.ai.prompts import EXTRACT_FORM_FIELD_PROMPT

class FormValue(BaseModel):
    field_number: int
    field_value: str | int | None
    

class DeclarationFormPlugin:
    def __init__(
        self,
        openai_client: AsyncOpenAI,
        openai_model_name: str
    ):
        self.openai_client = openai_client
        self.openai_model_name = openai_model_name
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)


    @kernel_function(
        name="process_declaration_form_message",
        description="Processes a message related to a declaration form",
    )
    async def process_declaration_form_message(
        self,
        message: str
    ) -> str:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        with open(f"{script_dir}/data/form_rules.json", 'r', encoding='utf-8') as fields_file:
            fields_data = json.load(fields_file)["fields"]

        self.logger.info(f"Found {len(fields_data)} fields in the form rules")

        prompts = []
        for field in fields_data:
            field_as_string = json.dumps(field, ensure_ascii=False)
            prompt = EXTRACT_FORM_FIELD_PROMPT.format(
                user_message=message,
                field_description=field_as_string
            )
            prompts.append(prompt)

        tasks = [self.fetch_response(prompt) for prompt in prompts]
        responses = await asyncio.gather(*tasks)

        missing_fields = []
        for i, response in enumerate(responses):
            if response["field_value"] is None:
                missing_fields.append(fields_data[i])

        return json.dumps(missing_fields, indent=4, ensure_ascii=False)


    async def fetch_response(self, prompt: str):
        response = await self.openai_client.beta.chat.completions.parse(
            model=self.openai_model_name,
            messages=[{'role': 'user', 'content': prompt}],
            response_format=FormValue
        )
        return response.choices[0].message.parsed   
