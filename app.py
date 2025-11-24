import os
import json
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
# TODO: is 'tools' needed?
tool_definition = extract.definition
tools = [extract]
tool_registry = {
    "extract_web_content": extract.extract
}

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

# construct input as user message
usr_input = f"Analyze this article: {check_url}"

prompt = prompt_object.build(input=usr_input)
response = client.chat.completions.create(**prompt)
# TODO: need to execute the tool call and add msg

# get tool calls from the response
choice = response.choices[0].message
tool_calls = choice.tool_calls

# execute tool calls
tool_results = []
for call in tool_calls:
    fn = tool_registry[call.function.name]
    args = json.loads(call.function.arguments)
    result = fn(**args)
    tool_results.append({
        "role": "tool",
        "tool_call_id": call.id,
        "content": json.dumps(result)
    })

# add chat history and tool call result
followup = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[
        {"role": "user", "content": usr_input},
        choice,
        *tool_results
    ]
)

pprint(followup.choices[0].message)
