import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from braintrust import init_logger, load_prompt, wrap_openai, traced, start_span
from pprint import pprint
from tools import extract

load_dotenv()
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
# NOTE: DON'T use 'x-bt-parent' header in this context.
# This header is meant for the proxy to know where to log traces, 
# but when you use wrap_openai with init_logger, the SDK handles context propagation automatically.
# Will result in broken spans.
client = wrap_openai(OpenAI(
    base_url="https://api.braintrust.dev/v1/proxy",
    api_key=braintrust_api_key,
    default_headers={"x-bt-use-cache": "always", 
                    "Cache-Control": "max-age=1209600"
                    },
))

@traced
def analyze(url: str):
    usr_input = f"Is this article biased?: {url}"
    prompt = prompt_object.build(input=usr_input)
    response = client.chat.completions.create(**prompt)

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
    
    return {"tool_results": tool_results, "choice": choice, "usr_input": usr_input}

@traced
def respond(analyze_results):
        # add chat history and tool call result
        followup = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "user", "content": analyze_results["usr_input"]},
                analyze_results["choice"],
                *analyze_results["tool_results"]
            ]
        )

        pprint(followup.choices[0].message)


def main():
    # create a root span to nest all function child spans under
    with start_span(name="Analyze Article", type="llm") as span:
        # URL of content to classify
        check_url = os.getenv("URL")
        # construct input as user message
        analyze_results = analyze(check_url)
        respond(analyze_results)
        span.log(input=check_url, output=analyze_results)
        # send spans to Braintrust before program exit
        logger.flush()

if __name__ == "__main__":
    main()