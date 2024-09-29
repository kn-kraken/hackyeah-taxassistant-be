import logging
from typing import Dict, List, Union

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AsyncOpenAI, OpenAI
from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import KernelArguments
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings

from app.services.ai.plugins import DeclarationFormPlugin, TaxDataPlugin
from app.services.ai.prompts import SYSTEM_PROMPT_DEFAULT


class LLMOrchestrator:
    def __init__(
        self, 
        chat_completion_service: OpenAIChatCompletion,
        chat_execution_settings: OpenAIChatPromptExecutionSettings,
        plugins: List[Union[DeclarationFormPlugin, TaxDataPlugin]],
        system_prompt: str = SYSTEM_PROMPT_DEFAULT,
    ):
        self.kernel: Kernel = Kernel()
        self.chat_completion_service = chat_completion_service
        self.chat_execution_settings = chat_execution_settings
        self.system_prompt = system_prompt

        for plugin in plugins:
            self.kernel.add_plugin(
                plugin=plugin,
                plugin_name=plugin.__class__.__name__,
            )

        self.conversations: Dict[str, ChatHistory] = {}
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        

    async def process_message(self, message: str, conversation_id: str) -> str:
        self.logger.info(f"Processing message: {message}")
        if conversation_id not in self.conversations:
            self.logger.info(f"Creating new conversation: {conversation_id}")
            chat_history = ChatHistory()
            chat_history.add_system_message(self.system_prompt)
        else:
            chat_history = self.conversations[conversation_id]
        
        chat_history.add_user_message_str(message)

        response = (await self.chat_completion_service.get_chat_message_contents(
            kernel = self.kernel,
            settings=self.chat_execution_settings,
            chat_history=chat_history,
            arguments=KernelArguments(),
        ))[0]
        response_text = str(response)
        self.logger.info(f"Response: {response_text}")
        chat_history.add_assistant_message_str(response_text)
        
        self.conversations[conversation_id] = chat_history

        return response_text

    
    @classmethod
    def OpenAI(
        cls,
        api_key: str,
        model_name: str,
        azure_search_key: str,
        azure_search_endpoint: str,
        azure_search_index_name: str,
    ) -> "LLMOrchestrator":
        completion_service_id = "chat-completion"
        openai_chat_completion_service = OpenAIChatCompletion(
            service_id=completion_service_id,
            ai_model_id=model_name,
            api_key=api_key,
        )
        execution_settings = OpenAIChatPromptExecutionSettings(
            service_id=completion_service_id,
            temperature=0.2,
            tool_choice="auto",
        )
        execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        credentials = AzureKeyCredential(azure_search_key)
        search_client = SearchClient(
            endpoint=azure_search_endpoint, 
            index_name=azure_search_index_name, 
            credential=credentials
        )
        openai_client = OpenAI(api_key=api_key)
        tax_data_plugin = TaxDataPlugin(search_client, openai_client)

        async_openai_client = AsyncOpenAI(api_key=api_key)    
        declaration_form_plugin = DeclarationFormPlugin(async_openai_client, model_name)
        plugins = [tax_data_plugin, declaration_form_plugin]

        return cls(
            chat_completion_service=openai_chat_completion_service,
            chat_execution_settings=execution_settings,
            plugins=plugins,
        )
    
