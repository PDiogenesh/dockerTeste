import os

from locust import HttpUser, constant, task


def _target_paths():
    paths = os.getenv("TARGET_PATHS", "/?p=1")
    return [path.strip() for path in paths.split(",") if path.strip()]


class WordpressUser(HttpUser):
    # Sem espera entre tarefas: usuarios fazem requisicoes continuamente
    wait_time = constant(0)

    @task
    def view_posts(self):
        for path in _target_paths():
            self.client.get(path, name=path)
