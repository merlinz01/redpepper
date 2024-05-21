import ssl

import hypercorn
from fastapi import FastAPI
from hypercorn.trio import serve
from trio import Event


class APIServer:
    def __init__(self, manager, config):
        self.manager = manager
        self.config = config
        self.app = FastAPI()
        self.app.add_api_route("/api/v1/agents", self.get_agents)
        self.app.add_api_route("/api/v1/agents/connected", self.get_connected_agents)
        self.hconfig = config = hypercorn.Config()
        self.hconfig.bind = [
            f"{self.config['api_bind_host']}:{self.config['api_bind_port']}"
        ]
        self.hconfig.certfile = self.config["api_tls_cert_file"]
        self.hconfig.keyfile = self.config["api_tls_key_file"]
        self.hconfig.keyfile_password = self.config["api_tls_key_password"]

    async def run(self):
        self.shutdown_event = Event()
        await serve(self.app, self.hconfig, shutdown_trigger=self.shutdown_event.wait)

    async def shutdown(self):
        self.shutdown_event.set()

    async def get_agents(self):
        return {"agents": self.manager.datamanager.get_agents()}

    async def get_connected_agents(self):
        return {"agents": self.manager.connected_agents()}
