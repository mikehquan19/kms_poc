import json
import os
import random
from pathlib import Path

from locust import HttpUser, LoadTestShape, between, task, events

# Load the provisioned keys
key_file = Path(__file__).with_name("generated_keys.json")
with key_file.open() as file:
    generated_keys = json.load(file)

public_keys = [entry["api_key"] for entry in generated_keys if not entry["internal"]]
if len(public_keys) == 0:
    raise RuntimeError("No public API keys found")

internal_keys = [entry["api_key"] for entry in generated_keys if entry["internal"]]
if len(internal_keys) == 0:
    raise RuntimeError("No internal API keys found")


class ProductionLoadShape(LoadTestShape):
    stages = [
        {"duration": 60, "users": 100, "spawn_rate": 20},
        {"duration": 180, "users": 350, "spawn_rate": 25},
        {"duration": 300, "users": 670, "spawn_rate": 30},
        {"duration": 1200, "users": 1000, "spawn_rate": 20},
        {"duration": 1260, "users": 100, "spawn_rate": 50},
    ]

    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]

        return None


class BaseAPIUser(HttpUser):
    abstract = True
    wait_time = between(1, 1.5)


class PublicAPIUser(BaseAPIUser):
    """
    User who got provisioned key that has access to only public endpoint
    """

    # Approximately 5 public users for every internal user.
    weight = 5

    def on_start(self):
        self.api_key = random.choice(public_keys)

    @task
    def get_animals(self):
        self.client.get(
            "/api/animals",
            headers={"x-api-key": self.api_key},
            name="/api/animals",
        )


class InternalAPIUser(BaseAPIUser):
    """
    User who got provisioned key that has access to both public and internal endpoints
    """

    weight = 1

    def on_start(self):
        self.api_key = random.choice(internal_keys)

    @task
    def get_animals(self):
        self.client.get(
            "/api/animals",
            headers={"x-api-key": self.api_key},
            name="/api/animals",
        )

    @task
    def get_internal(self):
        self.client.get(
            "/api/internal",
            headers={"x-api-key": self.api_key},
            name="/api/internal",
        )


@events.test_stop.add_listener
def print_final_statistics(environment, **kwargs):
    stats = environment.stats.total

    print("\n===== FINAL LOAD-TEST RESULTS =====")
    print(f"Total requests: {stats.num_requests}")
    print(f"Total failures: {stats.num_failures}")
    print(f"Failure rate: {stats.fail_ratio * 100:.2f}%")
    print("===================================")
