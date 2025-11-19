import extract
import os

def main(url):
    result = extract.extract(url)
    print(result)

# test the tool, set env var
if __name__ == "__main__":
    url = os.getenv("URL")
    if url:
        main(url)
    else:
        print("Empty URL")
        exit(1)
