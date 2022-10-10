import requests
import json
import time


headers = {
    "Content-Type": "application/json",
}

with open("wb-bot/api_queries/warehouseList.json", "r", encoding="utf-8") as f:
    warehouses = json.load(f)
    warehouses = warehouses["result"]["warehouses"]
    result = []
    for warehouse in warehouses:
        warehouseId = warehouse.get("id")
        payload = json.dumps(
            {
                "params": {"dateFrom": "2022-10-03", "dateTo": "2022-10-13", "warehouseId": warehouseId},
                "jsonrpc": "2.0",
                "id": "json-rpc_13",
            }
        )

        response = requests.request("POST", url, headers=headers, data=payload)
        time.sleep(0.2)
        data = response.json()
        try:
            if data["result"]["limits"]:
                tmp = {
                    "warehouseId": warehouseId,
                    "displayName": warehouse.get("displayName"),
                    "limits": data["result"]["limits"][str(warehouseId)],
                }
                result.append(tmp)
        except Exception as e:
            print(e)
            continue

    with open("wb-bot/api_queries/warehouse_limits.json", "a") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
