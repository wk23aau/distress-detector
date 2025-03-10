import requests

headers = {
    'Authorization': f'token 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'
}

response = requests.get(
    'https://api.github.com/repos/wk23aau/distress-detector',
    headers=headers
)

print(response.status_code)  # Should return 200
print(response.json())