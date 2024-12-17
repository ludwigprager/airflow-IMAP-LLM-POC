# https://docs.smith.langchain.com/prompt_engineering/tutorials/optimize_classifier

import os
from openai import OpenAI

client = OpenAI(
    base_url=os.environ.get("RUNPOD_BASE_URL"),
    api_key=os.environ.get("RUNPOD_API_KEY"),
)

available_topics = [
    "job-offer",
    "status-report",
    "newsletter",
    "private-message",
    "other",
    "spam",
    "invoice",
]

prompt_template = """Classify the type of the issue as one of {topics}.

Here are examples:
"ionos1 status report"                       "status-report"
"C++ SOFTWARE ENGINEER – REMOTE (6 MONTHS+)" "job-offer"
""                                           "other"
"rezeptfrei einkaufen"                       "spam"

Respond with just two words: X Y
X shall be your classification
Y shall be the percentage of accuracy: 100 for 'high accuracy' down to 0 for 'low accuracy'

Issue: {text}

"""


prompt_template_alt = """Classify the type of the issue as one of {topics}.
Respond with just one word and the likelyhood: X Y

Issue: {text}"""



def subject_classifier( subject: str):

    print("subject_classifier{}".format(len(subject)))
    # Create input for the model
    prompt = prompt_template.format(
        topics=','.join(available_topics),
        text=subject,
    )

    print("prompt: {}".format(prompt))
    
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

    print("classification result: {}".format(result))

    classification = result.choices[0].message.content
    return classification

