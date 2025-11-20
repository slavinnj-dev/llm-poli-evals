import braintrust
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from tavily import TavilyClient

load_dotenv()
tavily_key = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=tavily_key)
braintrust_project_name = os.getenv("BRAINTRUST_PROJECT_NAME")

project = braintrust.projects.create(braintrust_project_name)

class Args(BaseModel):
    url: str

definition = {
    "type": "function",
    "function": {
      "name": "extract_web_content",
      "description": "Extracts content from a web page",
      "parameters": {
        "required": [
          "url"
        ],
        "additionalProperties": False,
        "properties": {
          "url": {
            "type": "string",
            "description": "The URL of the web page to extract content from"
          }
        },
        "type": "object"
      },
      "strict": True
    }
  }

def extract(url: str):
    urls = [url]
    response = tavily_client.extract(urls=urls, include_images=False, extract_depth="advanced")
    return response

extractor = project.tools.create(name="Extract Web Content", 
                                       handler=extract, 
                                       parameters=Args, 
                                       slug = 'extract-web-content',
                                       if_exists='replace')