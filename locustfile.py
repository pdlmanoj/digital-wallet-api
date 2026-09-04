from locust import HttpUser, between, task


class WalletUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def check_blog(self):
        self.client.get("/health-check")
