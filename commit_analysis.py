import logging
import os
from collections import defaultdict
from dotenv import load_dotenv
import lorem # Used for testing

# Langchain imports
from langchain.schema import StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from chromadb.config import Settings as ChromaSettings
from langchain.prompts import (
    ChatPromptTemplate,
    PromptTemplate,
    SystemMessagePromptTemplate
)
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.docstore.document import Document
from langchain_core.runnables import RunnablePassthrough

# Local application imports
from utility import Utility
from git_repo_manager import GitRepoManager


# Configure logging
load_dotenv()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL)

langchain_verbosity = os.getenv("VERBOSE", "").lower() == "true"
if langchain_verbosity:
    from langchain.globals import set_debug
    set_debug(True)      


class CodeSummarization:

    # Used for Testing
    simulate = False

    def __init__(self):
        # Load environment variables
        self.dev_dir = os.getenv("DEVPATH", ".")
        
        # Load embedding_function once
        self.model_name = "sentence-transformers/all-mpnet-base-v2"
        self.embedding_function = SentenceTransformerEmbeddings(model_name=self.model_name)
        
        # Load LLM once
        temperature = 0.1
        max_tokens = 512
        self.llm = Utility.load_LLM(temperature=temperature, max_tokens=max_tokens)

    def get_code_summary(self, commit, code_diff):
        try:
            if self.simulate:
                return lorem.paragraph()
            summary,all_changes = self.process_code_diff(commit, code_diff)
            return self.format_summary(summary,all_changes)
        except Exception as e:
            raise e

            
    def process_code_diff(self, commit, code_diff):

        try:
            summary = defaultdict(list)

            # Get list of added/removed files
            git_repo_manager = GitRepoManager()
            existing_files, all_changes = git_repo_manager.extract_filenames(code_diff)
            file_diffs = git_repo_manager.parse_diff_files(code_diff)

            existing_files = sorted(existing_files)

            # Load code files
            documents = self.load_documents(existing_files, commit, file_diffs)

            # Process each file
            for file in existing_files:
                results = self.process_file(file, documents)
                summary[file].append(results)

            return summary,all_changes
        except Exception as e:
            raise e
    
    def load_documents(self, existing_files, commit, file_diffs):

        try:
            documents = []
            git_repo_manager = GitRepoManager()
            for file in existing_files:
                git_file_raw = git_repo_manager.get_raw_file_content(commit, file)
                file_diff = file_diffs[file]
                doc_raw = Document(page_content=git_file_raw, metadata={"source": self.dev_dir + f"/{file}"})
                doc_diff = Document(page_content=file_diff, metadata={"source": self.dev_dir + f"/{file}"})
                documents.extend([doc_raw, doc_diff])
            return documents
        except Exception as e:
            raise e
    
    def format_docs(self,docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def process_file(self, file, documents):
        try:
            filepath = self.dev_dir + f"/{file}"
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
            docs = text_splitter.split_documents(documents)

            vectorstore = Chroma.from_documents(docs, self.embedding_function, client_settings=ChromaSettings(anonymized_telemetry=False))
            retriever = vectorstore.as_retriever(search_kwargs={"k": 10, "filter": {"source": {"$eq": filepath}}})
            reviewer_prompt = self.code_reviewer_prompt()

            rag_chain = (
                {"code_diff": retriever | self.format_docs, "question": RunnablePassthrough()}
                | reviewer_prompt
                | self.llm
                | StrOutputParser()
            )

            logging.info(f"Processing {filepath}")
            return rag_chain.invoke("List the main changes made in the code, following the above guidelines.")
        except Exception as e:
            logging.error("Error processing file %s: %s", file, e, exc_info=True)
            return "Error in processing file."


    def format_summary(self, summary, all_changes):
        result_string = ""
        for key in summary:
            result_string += f"{key}:\n{summary[key][0]}\n\n"

        for change in all_changes:
                    for key, value in change.items():
                        result_string += f"{key} file: {value}"

        overall_summary = self.overall_summary(result_string)

        return overall_summary


    @staticmethod
    def code_reviewer_prompt():

        system = """
You are an expert in summarizing git commit differences for software developers. Provide clear, concise commit messages based on the provided git diff. Avoid technical jargon, unless necessary.

## Input Guidelines ##
- Analyze code changes shown in the standard git diff format.
- '+' indicates added code; '-' indicates removed code.
- Summarize functional changes without including actual code or sensitive details.
- Ignore non-functional parts, such as comments or AI prompts.
- Focus on added or removed functionalities.
- Ensure each line of your response is under 72 characters for standard commit message formatting.
- Respond in plaintext without markup or additional notes.

"""

        user = """
Code Differences:
|-Start--------------|>
{code_diff}
<|-End----------------|


## Inquiry ##
{question}


Response:
"""
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", 
                    Utility.convert_tabs_and_spaces(system)
                ),
                (
                    "user", Utility.convert_tabs_and_spaces(user) 
                )
            ]
        )
        return prompt
    

    def overall_summary(self,result):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
As a specialist in crafting commit messages, your task is to concisely summarize code modifications. Keep the following guidelines in mind:
* Start each message with a verb in the imperative mood (e.g., Update, Add, Refactor, Remove).
* Clearly highlight both additions and removals, including any files or functionalities that are added or removed.             
* Focus on the functional changes without delving into too much implementation detail.
* Keep each line of your response within 72 characters for readability in various tools.
* Ensure clarity and brevity in your descriptions.
* Begin each message with a reference to the specific file or functionality being modified, especially in multi-file changes.
* Provide responses as a list of bullet points in plain, unformatted text. Strictly avoid any markup or special formatting.
* Do not include actual code, confidential information, or AI prompts in your summaries.
"""),
            ("user", """
{input}:
             
{result_text}


Your task is to compose a distinct commit message for each file, summarizing the changes made, and ensuring to note any additions or removals as per the guidelines.
Your responses should be formatted as bullet points for each file, clearly summarizing the changes without markup.
""")
        ])

        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke({"input": "Based on the file summaries provided, create a commit message for each file. Structure each message as a list of bullet points, clearly stating the changes made. Remember to include both additions and removals, and adhere strictly to the format outlined","result_text":result})
      

class CommitMsgComparison:
    DEFAULT_TEMPERATURE = 0.1

    @staticmethod
    def compare_messages(original_commit_msg, generated_commit_msg):

        try:
            llm = Utility.load_LLM(temperature=CommitMsgComparison.DEFAULT_TEMPERATURE)
            output_parser = StrOutputParser()
            prompt = CommitMsgComparison.commit_reviewer_prompt()
            chain = prompt | llm | output_parser
            response = chain.invoke({"original_commit_msg": {original_commit_msg}, "generated_commit_msg": {generated_commit_msg}})
            confidence_int = Utility.parse_confidence(response)
            return confidence_int
           
        except Exception as e:
            logging.error(f"Error generating answer: {e}")
            raise ValueError("Error generating answer.") from e

    @staticmethod
    def commit_reviewer_prompt():
        return ChatPromptTemplate(
            input_variables=['original_commit_msg', 'generated_commit_msg'],
            messages=[
                SystemMessagePromptTemplate(
                    prompt=PromptTemplate(
                        input_variables=[],
                        template="""
Evaluate whether the original git commit message aligns with the generated one in terms of overall themes and main subjects. Your assessment should focus on the general alignment of the key themes and subjects mentioned in the messages, rather than on detailed exactness or specific wording.

ORIGINAL COMMIT MESSAGE:
{original_commit_msg}

GENERATED COMMIT MESSAGE:
{generated_commit_msg}


Task:
Based on a broad perspective, do the original and generated commit messages align in terms of overall themes and main subjects? Provide your answer as a confidence percentage, where 100% means complete confidence in alignment and 0% means no confidence.
Do not explain or provide a summary or markup.

Response:
Confidence: [Your Confidence Percentage]


"""
                    )
                )
            ]
        )