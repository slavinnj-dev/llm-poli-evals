import os
from dotenv import load_dotenv
from openai import OpenAI
from braintrust import init_logger, load_prompt, wrap_openai
from pprint import pprint
from tools import extract

load_dotenv()
# URL of content to classify
check_url = os.getenv("URL")
braintrust_api_key = os.getenv("BRAINTRUST_API_KEY")
braintrust_project_id = os.getenv("BRAINTRUST_PROJECT_ID")

# logger traces the OpenAI client calls
logger = init_logger(project="PoliticalSlant", api_key=braintrust_api_key)

# setup tools
tool_definition = extract.definition
tools = [extract]

# load the prompt from Braintrust, specify a version to load different variants
prompt_object = load_prompt(project="PoliticalSlant", 
                            slug="political-slant",
                            defaults={"tools": [extract.definition], "tool_choice": "required", "stream": False}
                            )

# x-bt-parent necessary to trace requests made over the proxy
# must include 'project_id' to avoid improper SpanComponents error
client = wrap_openai(OpenAI(
    base_url="https://api.braintrust.dev/v1/proxy",
    api_key=braintrust_api_key,
    default_headers={"x-bt-use-cache": "always", 
                     "Cache-Control": "max-age=1209600",
                     "x-bt-parent": f"project_id:{braintrust_project_id}"
                     },
))
prompt = prompt_object.build(input=check_url)
response = client.chat.completions.create(**prompt)
# TODO: need to execute the tool call and add msg
pprint(response)