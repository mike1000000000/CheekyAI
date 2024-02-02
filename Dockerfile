FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Create a directory intended for volume mount
RUN mkdir /repo

# Mark the directory as a mount point
VOLUME /repo

# Update package lists, install Git, and clean up the cache to keep the image small
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

RUN git config --global --add safe.directory /repo    

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Inline command to preload the pytorch model
RUN python -c "from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings; SentenceTransformerEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2')"

# Define environment variables
ENV MAINBRANCH=main
ENV DEVPATH=/repo 
ENV VERBOSE=False
ENV LOG_LEVEL=ERROR
ENV MODEL=gpt-3.5-turbo-1106
ENV CONFIDENCE=60

# Run script.py when the container launches
ENTRYPOINT ["python", "cheekyAI.py"]