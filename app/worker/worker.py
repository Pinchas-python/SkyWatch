import json
import os
import time

import pika
import requests

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "skywatch-rabbitmq")
QUEUE_NAME = "weather_requests"


def get_weather(city):
    geo_response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
        timeout=10,
    )
    geo_response.raise_for_status()

    locations = geo_response.json().get("results", [])
    if not locations:
        raise ValueError(f"City not found: {city}")

    location = locations[0]

    weather_response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current": "temperature_2m,wind_speed_10m",
        },
        timeout=10,
    )
    weather_response.raise_for_status()

    current = weather_response.json()["current"]

    return {
        "city": location["name"],
        "temperature": current["temperature_2m"],
        "wind_speed": current["wind_speed_10m"],
    }


def process_message(ch, method, properties, body):
    try:
        data = json.loads(body)
        city = data["city"]

        print(f"Processing weather request: {city}", flush=True)

        result = get_weather(city)

        print(f"Weather result: {json.dumps(result)}", flush=True)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except (ValueError, KeyError, TypeError) as error:
        print(f"Invalid request: {error}", flush=True)
        ch.basic_reject(
            delivery_tag=method.delivery_tag,
            requeue=False,
        )

    except requests.RequestException as error:
        print(f"Weather API error: {error}", flush=True)
        ch.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=False,
        )


while True:
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST)
        )

        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        channel.basic_qos(prefetch_count=1)

        channel.basic_consume(
            queue=QUEUE_NAME,
            on_message_callback=process_message,
        )

        print("Worker waiting for messages...", flush=True)
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError:
        print("RabbitMQ unavailable. Retrying...", flush=True)
        time.sleep(5)

