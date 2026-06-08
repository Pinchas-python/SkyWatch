import json
import os
import time

import pika
import requests


RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "weather_requests")


def geocode_city(city: str):
    response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "en", "format": "json"},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    results = data.get("results") or []
    if not results:
        return None
    return results[0]


def get_current_weather(latitude: float, longitude: float):
    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": latitude, "longitude": longitude, "current": "temperature_2m,wind_speed_10m"},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("current", {})


def process_message(ch, method, properties, body):
    try:
        payload = json.loads(body.decode("utf-8"))
        print(f"[worker] received payload={payload}", flush=True)
        city = payload.get("city", "").strip()
        request_id = payload.get("request_id", "unknown")

        if not city:
            print(f"[worker] empty city request_id={request_id}", flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        location = geocode_city(city)
        if not location:
            print(f"[worker] city not found request_id={request_id} city={city}", flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        weather = get_current_weather(location["latitude"], location["longitude"])
        temp = weather.get("temperature_2m")
        wind = weather.get("wind_speed_10m")

        print(
            "[worker] request_id={} city={} country={} temp_c={} wind_kmh={}".format(
                request_id,
                location.get("name"),
                location.get("country"),
                temp,
                wind,
            ),
            flush=True,
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:
        print(f"[worker] processing failed: {exc}", flush=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST)
            )
            channel = connection.channel()
            channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=process_message)
            print("[worker] waiting for messages...", flush=True)
            channel.start_consuming()
        except Exception as exc:
            print(f"[worker] rabbitmq not ready, retrying in 5s: {exc}", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
