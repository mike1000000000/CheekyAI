import os
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

URI = os.getenv("URI","")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY","")
MODEL= os.getenv("MODEL","gpt-3.5-turbo")

class Utility():
    
    @staticmethod
    def cleanTripleQuotes(input_string):
        # Replace triple-quoted double quotes with triple-quoted single quotes
        return input_string.replace('"""', "'''")
        
    
    @staticmethod
    def cleanTripleSlashes(input_string: str) -> str:
        # Replace multiple slashes with single slashes
        return input_string.replace("\\\\", "\\")
        
    
    @staticmethod
    def remove_spaces_and_punctuation(input_string: str) -> str:
        cleaned_list = [char for char in input_string if char.isalnum()]
        cleaned_string = ''.join(cleaned_list)
        return cleaned_string
    
    @staticmethod
    def get_first_word(sentence: str) -> str:
        try:
            first_word = sentence.split()[0]
            cleaned = Utility.remove_spaces_and_punctuation(first_word.lower())
            return cleaned
        
        except Exception as e:
            raise ValueError("Error getting first word.") from e

    @staticmethod
    def parse_confidence(sentence: str) -> int:
        try:
            parts = sentence.split(":")

            if len(parts) >= 2:
                # The second part is the number, strip any whitespace and percentage
                confidence_number = parts[1].strip().rstrip('%')
                return int(confidence_number)
            else:
                raise Exception("Could not parse confidence.")

        
        except Exception as e:
            raise ValueError("Error getting confidence.") from e

    @staticmethod
    def load_LLM(**kwargs) -> ChatOpenAI:
        model = MODEL

        optional_params = {
            "top_p": 0.2,
            "frequency_penalty": 1,
            "presence_penalty":1,
        }

        if URI:
            kwargs['base_url'] = URI

        return ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=model,
            model_kwargs=optional_params,
            **kwargs
        )
    
    @staticmethod
    def convert_tabs_and_spaces(input_str: str) -> str:
        # Convert tabs to spaces using expandtabs
        spaces_expanded = input_str.expandtabs()
        # Replace consecutive spaces with a single space
        spaces_single = re.sub(r'\s+', ' ', spaces_expanded)

        return spaces_single