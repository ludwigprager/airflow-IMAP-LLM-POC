# https://docs.smith.langchain.com/prompt_engineering/tutorials/optimize_classifier

import os
from openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter

client = OpenAI(
    base_url=os.environ.get("RUNPOD_BASE_URL"),
    api_key=os.environ.get("RUNPOD_API_KEY"),
)

available_topics = [
    "job offer",
    "status report",
    "newsletter",
    "private message",
    "other",
    "invoice",
]

prompt_template = """Classify the type of the issue as one of {topics}.
Respond with just one word: X

Issue: {text}"""


def email_classifier( email: str):

#   splitter = CharacterTextSplitter(character_limit=500)

    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", " ", ""],
        chunk_size=8000,
        chunk_overlap=200,
        length_function=len
    )

    chunks = splitter.split_text(email)

    # Classify each chunk
    classifications = [email_classifier_chunk(chunk) for chunk in chunks]
    print("chunk classifications:: {}".format(classifications))

    # Combine classifications (e.g., majority voting)
    final_classification = max(set(classifications), key=classifications.count)

    print("final: {}".format(final_classification))

    return final_classification

def email_classifier_chunk( email: str):

    print("email_classifier_chunk {}".format(len(email)))
    # Create input for the model
    prompt = prompt_template.format(
        topics=','.join(available_topics),
        text=email,
    )
    
    result = client.chat.completions.create(
    #   model="openchat/openchat_3.5",
        model="openchat/openchat-3.6-8b-20240522",
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    print("chunk result: {}".format(result))

    classification = result.choices[0].message.content
    return classification

