import json
import os
import uuid

from flask import Flask, redirect, render_template_string, request, url_for
import pika


RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "weather_requests")

app = Flask(__name__)

INDEX_HTML = """
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>SkyWatch</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 2rem; background: #f5f7fb; }
      .card {
        max-width: 560px; margin: 0 auto; background: #fff; padding: 1.25rem;
        border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.08);
      }
      h1 { margin-top: 0; }
      input, button { width: 100%; padding: 0.7rem; margin-top: 0.6rem; font-size: 1rem; }
      button { cursor: pointer; background: #1677ff; color: #fff; border: 0; border-radius: 8px; }
      .ok { color: #096c2b; }
      .err { color: #c62828; }
      code { background: #f1f3f5; padding: 0.1rem 0.3rem; }
    </style>
  </head>
  <body>
    <div class=\"card\">
      <h1>SkyWatch</h1>
      <p>Submit a city. The worker will fetch weather data from Open-Meteo.</p>
      {% if message %}
        <p class=\"{{ message_class }}\">{{ message }}</p>
      {% endif %}
      <form method=\"post\" action=\"{{ url_for('submit_city') }}\">
        <label for=\"city\">City</label>
        <input id=\"city\" name=\"city\" placeholder=\"Tel Aviv\" required />
        <button type=\"submit\">Send Request</button>
      </form>
      <p>Queue name: <code>{{ queue_name }}</code></p>
    </div>
  </body>
</html>
"""


def publish_message(city: str) -> str:
    request_id = str(uuid.uuid4())
    payload = {"request_id": request_id, "city": city.strip()}

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    channel.basic_publish(
        exchange="",
        routing_key=RABBITMQ_QUEUE,
        body=json.dumps(payload).encode("utf-8"),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    connection.close()
    return request_id


@app.route("/", methods=["GET"])
def index():
    return render_template_string(
        INDEX_HTML,
        message=None,
        message_class="",
        queue_name=RABBITMQ_QUEUE,
    )


@app.route("/submit", methods=["POST"])
def submit_city():
    city = request.form.get("city", "").strip()
    if not city:
        return redirect(url_for("index"))

    try:
        request_id = publish_message(city)
        message = f"Request queued successfully. request_id={request_id}"
        message_class = "ok"
    except Exception as exc:
        message = f"Failed to publish message: {exc}"
        message_class = "err"

    return render_template_string(
        INDEX_HTML,
        message=message,
        message_class=message_class,
        queue_name=RABBITMQ_QUEUE,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
