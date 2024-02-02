# CheekyAI

![My Image](assets/cheekyAI_logo.png)

CheekyAI is an advanced tool designed to enhance the quality of commit messages in software development projects. Utilizing artificial intelligence, CheekyAI examines the content of code commits and suggests improvements to the associated commit messages, ensuring they accurately reflect the changes made.

# Features
* **AI-Powered Summarization**: Generates concise summaries of code changes to guide the creation of commit messages.
* **Specific Commit Processing**: Allows specifying a commit hash to process, facilitating targeted analysis of commits.
* **Commit Message Comparison**: Compares original and AI-generated commit messages to suggest improvements. If the comparison fails, CheekyAI will exit with error code 1.
* **Error Handling Flexibility**: Prevents CheekyAI from exiting with an error code if the comparison fails, enhancing usability in continuous integration pipelines.
* **Silent Mode**: Offers a silent mode, which suppresses banners and outputs only the suggested message. Note: This feature is not compatible with the compare option.
* **Multithreading for Efficiency**: Uses multithreading to perform AI operations and UI updates simultaneously, ensuring smooth user experience.
* **Rich Console Outputs**: Leveraging the rich library for enhanced console outputs and visual feedback.
* **Environment Variable Management**: Configurable settings using environment variables for flexibility.

## CheekyAI in Action
Here is an example of the CheekyAI output.

![CheekyAI Demo](assets/cheekyAI_docker.gif)

## Disclaimers
CheekyAI is provided "as is" and without warranties of any kind, either express or implied. The developers of CheekyAI disclaim all liability for any direct, indirect, incidental, or consequential damages that may result from the use of, or the inability to use CheekyAI, including but not limited to, data loss, system damage, or malfunctions. By using CheekyAI, users acknowledge and agree that they assume full responsibility for any risks associated with their use of the application.

### Usage Advisory
CheekyAI is developed for experimental and development use and is not intended for production environments. Deploying CheekyAI in production may lead to increased costs and potential stability issues. Users are advised against using it in such settings to avoid unforeseen complications.

### Note on Inference Service Costs
CheekyAI integrates with external AI inference services, such as OpenAI, to enhance commit message generation and offer other AI-powered features. Utilizing these services may result in additional costs. Users are strongly advised to familiarize themselves with the pricing structures and policies of any third-party services they engage with through CheekyAI.

CheekyAI is not responsible or liable for any costs incurred due to the use of these external services, whether those costs arise from regular usage, unexpected service behavior, or malfunctions. Responsibility for managing and understanding the implications of using such services rests solely with the user. Please ensure to conduct due diligence and consider potential costs carefully before leveraging external AI inference capabilities within CheekyAI.

## Requirements
Make sure you have the following dependencies installed before running the script:

- [Python](https://www.python.org/) (version 3.11 or higher)
- [Git](https://git-scm.com/)
- Access to an LLM API inference service (e.g. OpenAI, Textgen)
- Various Python libraries as listed in requirements.txt
- 8 Gb Disk space - CheekyAI incorporates an open-source embedded sentence transformer to generate embeddings locally, minimizing the need for API calls.


## Setup
1. Clone the repository.
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```
3. Configure the necessary environment variables in a .env file (copy the .env_example to .env): 
   - `DEVPATH`: Specify the development path where your project is located. This should be the absolute path on your system.
   - `OPENAI_API_KEY`: Add your OpenAI API key here to enable AI features. You can obtain this key from your OpenAI account dashboard.
   - `MAINBRANCH`: Name your primary branch (e.g., main or master). This is used by CheekyAI to determine the default branch for operations.

   Example .env file content:
   ```env
   VERBOSE=False
   LOG_LEVEL=ERROR
   MAINBRANCH=main
   DEVPATH=/path/to/your/source/code
   MODEL=gpt-3.5
   OPENAI_API_KEY=you-openai-api-key
   CONFIDENCE=60
   ```


## Usage
Run the script cheekyAI.py with the appropriate arguments to process commits in your repository. It can be used to process the latest commit or a specific commit in the current repository.

Basic Usage
```bash
python cheekyAI.py
```

For a specific commit:
```bash
python cheekyAI.py --commit <commit_hash>
```

To compare the current commit message with the generated one:
```bash
python cheekyAI.py --compare
```

For silent operation that only outputs the generated message without banners or progress bars:
```bash
python cheekyAI.py --silent
```

To avoid exiting with an error code if the comparison fails:
```bash
python cheekyAI.py --compare --nobreak
```

### Example
```bash
python cheekyAI.py --commit 5abcdefa3c79a962c1b219a611358250f1e635827 --compare --nobreak
```

## Docker
CheekyAI can be easily containerized using Docker, enabling a consistent and isolated environment for running the application. Below are the steps to build the Docker image and run CheekyAI within a Docker container.

### Building the Docker Image
To compile the Docker image, navigate to the root directory of the CheekyAI project where the Dockerfile is located, and run the following command:

```bash
docker build -t cheekyai .
```
**Note**: This image will be ~ 8 Gb.

### Running CheekyAI in a Docker Container
After building the image, you can run CheekyAI in a Docker container using the following command. This example shows how to run CheekyAI with default settings:

```bash
docker run --rm -v /path/to/your/source/code:/repo -e OPENAI_API_KEY="yourOpenAIApiKey" -e MAINBRANCH=main -t cheekyai
```

To run CheekyAI with specific arguments (e.g., processing a specific commit, comparison mode, silent operation, or avoiding exit with an error code), you can append the arguments to the end of the docker run command like so:

```bash
docker run --rm -v /path/to/your/source/code:/repo -e OPENAI_API_KEY="yourOpenAIApiKey" -e MAINBRANCH=main -t cheekyai --compare --nobreak
```
Here, --rm ensures that the container is removed after it exits, keeping your system clean.The -t option allocates a pseudo-terminal, supporting rich text features and progress bars within the Docker container.

# Credits
This project makes use of several open-source packages. We extend our gratitude to the developers and contributors of these projects:

- [chromadb](https://pypi.org/project/chromadb/): A lightweight and efficient database solution for Python applications. 
- [GitPython](https://pypi.org/project/GitPython/): A python library used to interact with Git repositories.
- [langchain](https://pypi.org/project/langchain/): A framework for building and experimenting with language models and applications.
- [lorem](https://pypi.org/project/lorem/): A simple lorem ipsum text generator for Python.
- [python-dotenv](https://pypi.org/project/python-dotenv/): Reads key-value pairs from a .env file and sets them as environment variables.
- [requests](https://pypi.org/project/requests/): A simple, yet elegant HTTP library for Python, built for human beings.
- [rich](https://pypi.org/project/rich/): A Python library for rich text and beautiful formatting in the terminal.
- [sentence-transformers](https://pypi.org/project/sentence-transformers/): A Python framework for state-of-the-art sentence and text embeddings.

Each of these packages has been instrumental in the development of this project, providing essential functionality that has contributed to our project's success. We encourage you to explore these projects and consider supporting them.


# License

This project is licensed under the MIT License - see the LICENSE.md file for details.