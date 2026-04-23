from flask import Flask, render_template, jsonify, request
import json
import requests

from gps_client import GPSDataStore, GPSWebSocketClient

app = Flask(__name__)

store = GPSDataStore()
gps_ws_client = GPSWebSocketClient("ws://localhost:4001", store)
gps_ws_client.start()

current_config = {
    "emulationZoneSize": 200,
    "messageFrequency": 1,
    "satelliteSpeed": 100,
    "objectSpeed": 10
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/data")
def get_data():
    data = store.get_data()
    data["config"] = current_config
    return jsonify(data)


@app.route("/api/config", methods=["POST"])
def update_config():
    global current_config

    data = request.get_json()

    try:
        response = requests.post(
            "http://localhost:4001/config",
            json=data,
            timeout=5
        )

        if response.ok:
            current_config.update(data)

        parsed_response = None
        response_text = response.text

        try:
            parsed_response = response.json()
        except Exception:
            try:
                parsed_response = json.loads(response.text)
            except Exception:
                parsed_response = response_text

        return jsonify({
            "success": response.ok,
            "status_code": response.status_code,
            "response": parsed_response
        }), response.status_code

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True)