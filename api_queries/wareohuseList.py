import requests
import json


payload = json.dumps({"jsonrpc": "2.0", "id": "json-rpc_11"})
headers = {
    "Content-Type": "application/json",
}

response = requests.request("POST", url, headers=headers, data=payload)
with open("warehouseList.json", "w", encoding="utf-8") as f:
    json.dump(response.json(), f, indent=4, ensure_ascii=False)
