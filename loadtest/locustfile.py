from locust import HttpUser, task, between, LoadTestShape
import os


class ProductionLoadShape(LoadTestShape):
    stages = [
        {"duration": 60, "users": 100, "spawn_rate": 20},
        {"duration": 120, "users": 200, "spawn_rate": 20},
        {"duration": 240, "users": 500, "spawn_rate": 20},
        {"duration": 340, "users": 50, "spawn_rate": 25},
    ]

    def tick(self):
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return (
                    stage["users"],
                    stage["spawn_rate"],
                )

        return None


class APIUser(HttpUser):
    wait_time = between(1, 1.5)

    def on_start(self):
        self.api_key = os.getenv("SAMPLE_API_KEY")

    @task
    def get_animals(self):
        self.client.get(
            "/api/animals",
            headers={
                "x-api-key": self.api_key,
            },
        )

    @task
    def get_new_key_and_animals(self):
        self.client.post()
