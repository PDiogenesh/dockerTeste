import os

from locust import HttpUser, between, task


def _target_paths():
    paths = os.getenv("TARGET_PATHS", "/?p=1")
    return [path.strip() for path in paths.split(",") if path.strip()]


class WordpressUser(HttpUser):
    wait_time = between(
        float(os.getenv("WAIT_TIME_MIN", "1")),
        float(os.getenv("WAIT_TIME_MAX", "3")),
    )

    @task
    def view_posts(self):
        for path in _target_paths():
            self.client.get(path, name=path)
