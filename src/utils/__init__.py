def format_request(endpoint, params):
    # Function to format the API request
    return {
        "url": f"https://api.bundestag.de/{endpoint}",
        "params": params
    }

def parse_response(response):
    # Function to parse the API response
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()