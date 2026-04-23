import math
from typing import List, Dict, Optional

import numpy as np
from scipy.optimize import minimize


SPEED_OF_LIGHT_KM_S = 300000.0


def calculate_distance_from_message(message: dict) -> Optional[float]:
    sent_at = message.get("sentAt")
    received_at = message.get("receivedAt")

    if sent_at is None or received_at is None:
        return None

    delta_seconds = (received_at - sent_at) / 1000.0

    if delta_seconds < 0:
        return None

    distance = SPEED_OF_LIGHT_KM_S * delta_seconds
    return distance


def build_satellite_data(messages: List[dict]) -> List[Dict]:
    satellites = []

    for msg in messages:
        satellite_id = msg.get("id")
        x = msg.get("x")
        y = msg.get("y")

        if satellite_id is None or x is None or y is None:
            continue

        distance = calculate_distance_from_message(msg)
        if distance is None:
            continue

        satellites.append({
            "id": satellite_id,
            "x": float(x),
            "y": float(y),
            "distance": float(distance),
        })

    return satellites


def trilateration_analytic(satellites: List[Dict]) -> Optional[Dict]:
    if len(satellites) < 3:
        return None

    s1, s2, s3 = satellites[:3]

    x1, y1, r1 = s1["x"], s1["y"], s1["distance"]
    x2, y2, r2 = s2["x"], s2["y"], s2["distance"]
    x3, y3, r3 = s3["x"], s3["y"], s3["distance"]

    a = 2 * (x2 - x1)
    b = 2 * (y2 - y1)
    c = r1**2 - r2**2 - x1**2 + x2**2 - y1**2 + y2**2

    d = 2 * (x3 - x1)
    e = 2 * (y3 - y1)
    f = r1**2 - r3**2 - x1**2 + x3**2 - y1**2 + y3**2

    denominator = a * e - b * d

    if abs(denominator) < 1e-9:
        return None

    x = (c * e - b * f) / denominator
    y = (a * f - c * d) / denominator

    return {"x": x, "y": y}


def loss_function(point: np.ndarray, satellites: List[Dict]) -> float:
    x, y = point
    total_error = 0.0

    for sat in satellites:
        predicted_distance = math.sqrt((x - sat["x"])**2 + (y - sat["y"])**2)
        error = predicted_distance - sat["distance"]
        total_error += error**2

    return total_error


def trilateration_numeric(satellites: List[Dict]) -> Optional[Dict]:
    if len(satellites) < 3:
        return None

    initial_x = sum(s["x"] for s in satellites) / len(satellites)
    initial_y = sum(s["y"] for s in satellites) / len(satellites)

    result = minimize(
        loss_function,
        x0=np.array([initial_x, initial_y]),
        args=(satellites,),
        method="Nelder-Mead"
    )

    if not result.success:
        return None

    return {"x": float(result.x[0]), "y": float(result.x[1])}