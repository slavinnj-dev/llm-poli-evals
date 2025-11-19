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

def extract(url: str):
    urls = [url]
    response = tavily_client.extract(urls=urls, include_images=False, extract_depth="advanced")
    return response

extractor = project.tools.create(name="Extract Web Content", 
                                       handler=extract, 
                                       parameters=Args, 
                                       slug = 'extract-web-content',
                                       if_exists='replace')