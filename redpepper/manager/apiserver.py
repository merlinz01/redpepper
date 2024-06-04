import datetime
import io
import logging
import os
import secrets
import time
import typing

import hypercorn
import pyotp
import trio
from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketException,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from hypercorn.trio import serve
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

logger = logging.getLogger(__name__)

# Silence hpack logging
import hpack.hpack

hpack.hpack.log.setLevel(logging.WARNING)
import hpack.table

hpack.table.log.setLevel(logging.WARNING)


class APIServer:
    def __init__(self, manager, config):
        from redpepper.manager.manager import Manager  # for type hint

        self.manager: Manager = manager
        self.config = config
        self.app = FastAPI()
        self.app.add_api_route("/api/v1/agents", self.get_agents)
        self.app.add_api_route("/api/v1/agents/names", self.get_agent_names)
        self.app.add_api_route("/api/v1/agents/connected", self.get_connected_agents)
        self.app.add_api_route("/api/v1/config/file", self.get_config_file)
        self.app.add_api_route(
            "/api/v1/config/file", self.save_config_file, methods=["POST"]
        )
        self.app.add_api_route(
            "/api/v1/config/file", self.delete_config_file, methods=["DELETE"]
        )
        self.app.add_api_route(
            "/api/v1/config/file", self.rename_config_file, methods=["PATCH"]
        )
        self.app.add_api_route(
            "/api/v1/config/file", self.create_config_file, methods=["PUT"]
        )
        self.app.add_api_route("/api/v1/config/tree", self.get_config_tree)
        self.app.add_api_route("/api/v1/command", self.command, methods=["POST"])
        self.app.add_api_route("/api/v1/events/since", self.get_eventlog_since)
        self.app.add_api_websocket_route("/api/v1/events/ws", self.event_channel)
        self.app.add_api_route("/api/v1/login", self.login, methods=["POST"])
        self.app.add_api_route("/api/v1/logout", self.logout, methods=["POST"])
        self.app.add_api_route(
            "/api/v1/verify_totp", self.verify_totp, methods=["POST"]
        )
        self.app.add_api_route("/api/v1/totp_qr", self.get_totp_qr)
        self.app.mount("/", StaticFiles(directory=config["api_static_dir"], html=True))
        self.app.add_middleware(CORSMiddleware)
        self.app.add_middleware(
            SessionMiddleware,
            secret_key=config["api_session_secret_key"],
            https_only=True,
            max_age=self.config["api_session_max_age"],
        )
        self.hconfig = config = hypercorn.Config()
        self.hconfig.loglevel = "INFO"
        self.hconfig.bind = [
            f"{self.config['api_bind_host']}:{self.config['api_bind_port']}"
        ]
        self.hconfig.certfile = self.config["api_tls_cert_file"]
        if os.stat(self.config["api_tls_cert_file"]).st_mode & 0o77 != 0:
            raise ValueError(
                "TLS key file %s is insecure, please set permissions to 600"
                % self.config["api_tls_cert_file"],
            )
        self.hconfig.keyfile = self.config["api_tls_key_file"]
        self.hconfig.keyfile_password = self.config["api_tls_key_password"]
        if not self.config["api_session_secret_key"]:
            raise ValueError("api_session_secret_key must be set in the configuration")
        if "changeme" in self.config["api_session_secret_key"]:
            logger.error(
                "Session secret key for API login is still set to a default value. This is insecure and must be changed."
            )

    async def run(self):
        self.shutdown_event = trio.Event()
        await serve(self.app, self.hconfig, shutdown_trigger=self.shutdown_event.wait)

    async def shutdown(self):
        logger.info("Shutting down API server")
        self.shutdown_event.set()

    def get_auth_for_user(self, username):
        logins = self.config["api_logins"]
        if not isinstance(logins, list):
            logger.warn("API logins is not a list")
            return None
        for login in logins:
            if not isinstance(login, dict):
                logger.warn("API login is not a dict")
                continue
            if "username" not in login:
                logger.warn("API login is missing username or password")
                continue
            if login["username"] == username:
                return login
        return None

    def check_credentials(self, username, password):
        logger.info("Checking credentials for user %s", username)
        starttime = time.monotonic()
        success = False
        login = self.get_auth_for_user(username)
        if login and login.get("password", "") and login["password"] == password:
            success = True
        else:
            logger.debug("Login failed for user %s", username)
        endtime = time.monotonic()
        # Add a constant time delay to make timing attacks harder
        CONSTANT_TIME = 0.01
        if endtime - starttime < CONSTANT_TIME:
            time.sleep(CONSTANT_TIME - (endtime - starttime))
        else:
            logger.warn(
                "Login check took too long, please open an issue on GitHub saying that you had a login check that took %s seconds.",
                endtime - starttime,
            )
            # If we overran the constant time, add some random delay to throw off timing attacks
            time.sleep(secrets.randbelow(10001) / 100000)  # 0-100ms
        return success

    def check_session(self, request):
        if not request.session.get("username", None):
            logger.debug("No username in session")
            raise HTTPException(status_code=401, detail="Not authenticated")
        if not request.session.get("otp_verified", False):
            logger.debug("OTP not verified")
            raise HTTPException(status_code=401, detail="Not authenticated")

    def check_totp(self, username, otp):
        logger.debug("Checking TOTP for user %s", username)
        login = self.get_auth_for_user(username)
        if login and "totp_secret" in login and isinstance(login["totp_secret"], str):
            secret = login["totp_secret"]
        else:
            logger.debug("No TOTP secret found for user %s", username)
            return False
        return pyotp.TOTP(secret, name=username, issuer="RedPepper API").verify(otp)

    def get_totp_qr_data(self, username):
        logger.debug("Generating TOTP QR code for user %s", username)
        try:
            import qrcode
        except ImportError:
            return None
        login = self.get_auth_for_user(username)
        if login and "totp_secret" in login and isinstance(login["totp_secret"], str):
            secret = login["totp_secret"]
        else:
            logger.debug("No TOTP secret found for user %s", username)
            return False
        uri = pyotp.TOTP(
            secret, name=username, issuer="RedPepper API"
        ).provisioning_uri()
        qr = qrcode.make(uri)
        stream = io.BytesIO()
        qr.save(stream, "PNG")
        return stream.getvalue()

    # API Endpoints

    async def event_channel(self, websocket: WebSocket):
        try:
            self.check_session(websocket)
        except HTTPException:
            raise WebSocketException(status.WS_1008_POLICY_VIOLATION)
        consumer = self.manager.eventlog.add_consumer()
        try:
            await websocket.accept()
            async for event in consumer:
                await websocket.send_json(event)
        finally:
            self.manager.eventlog.remove_consumer(consumer)

    async def command(self, request: Request, parameters: "CommandParameters"):
        self.check_session(request)
        try:
            connected = await self.manager.send_command(
                parameters.agent, parameters.command, parameters.args, parameters.kw
            )
            if not connected:
                return {
                    "success": False,
                    "detail": "Agent %r not connected" % parameters.agent,
                }
        except Exception as e:
            return {"success": False, "detail": str(e)}
        return {"success": True}

    async def create_config_file(
        self, request: Request, path: str, isdir: bool = False
    ):
        self.check_session(request)
        func = self.manager.datamanager.create_new_conf_file
        if isdir:
            func = self.manager.datamanager.create_new_conf_dir
        success, detail = await trio.to_thread.run_sync(func, path)
        return {"success": success, "detail": detail}

    async def delete_config_file(self, request: Request, path: str):
        self.check_session(request)
        success, detail = await trio.to_thread.run_sync(
            self.manager.datamanager.delete_conf_file, path
        )
        return {"success": success, "detail": detail}

    async def get_agents(self, request: Request):
        self.check_session(request)
        agents = []
        connected = self.manager.connected_agents()
        for agent in self.manager.datamanager.get_agents():
            agents.append(
                {
                    "id": agent,
                    "connected": agent in connected,
                }
            )
        return {"agents": agents}

    async def get_agent_names(self, request: Request):
        self.check_session(request)
        return {"agents": self.manager.datamanager.get_agents()}

    async def get_config_file(self, request: Request, path: str):
        self.check_session(request)
        data = await trio.to_thread.run_sync(
            self.manager.datamanager.get_conf_file, path
        )
        return {"success": data is not None, "content": data}

    async def get_config_tree(self, request: Request):
        self.check_session(request)
        tree = await trio.to_thread.run_sync(
            self.manager.datamanager.get_conf_file_tree
        )
        return {"tree": tree}

    async def get_connected_agents(self, request: Request):
        self.check_session(request)
        return {"agents": self.manager.connected_agents()}

    async def get_eventlog_since(self, request: Request, since: datetime.datetime):
        self.check_session(request)
        since = since.timestamp()
        return {"events": [event async for event in self.manager.eventlog.since(since)]}

    async def get_totp_qr(self, request: Request):
        self.check_session(request)
        qr_data = await trio.to_thread.run_sync(
            self.get_totp_qr_data, request.session["username"]
        )
        return Response(
            content=qr_data,
            media_type="image/png",
        )

    async def login(self, request: Request, credentials: "LoginCredentials"):
        if self.check_credentials(credentials.username, credentials.password):
            request.session["username"] = credentials.username
            request.session["otp_verified"] = False
            return {"success": True}
        else:
            request.session["username"] = None
            request.session["otp_verified"] = False
            return {"success": False}

    async def logout(self, request: Request):
        request.session["username"] = None
        request.session["otp_verified"] = False
        return {"success": True}

    async def rename_config_file(
        self, request: Request, path: str, new_path: "ConfigFileName"
    ):
        self.check_session(request)
        success, detail = await trio.to_thread.run_sync(
            self.manager.datamanager.rename_conf_file, path, new_path.path
        )
        return {"success": success, "detail": detail}

    async def save_config_file(
        self, request: Request, path: str, data: "ConfigFileContents"
    ):
        self.check_session(request)
        success, detail = await trio.to_thread.run_sync(
            self.manager.datamanager.save_conf_file, path, data.data
        )
        return {"success": success, "detail": detail}

    async def verify_totp(self, request: Request, totp: "TOTPCredentials"):
        username = request.session.get("username", None)
        if not username:
            return {"success": False, "detail": "not logged in"}
        if self.check_totp(username, totp.totp):
            request.session["otp_verified"] = True
            return {"success": True}
        request.session["username"] = None
        request.session["otp_verified"] = False
        return {"success": False, "detail": "invalid OTP"}


class LoginCredentials(BaseModel):
    username: str
    password: str


class TOTPCredentials(BaseModel):
    totp: str


class CommandParameters(BaseModel):
    agent: str
    command: str
    args: list[typing.Any]
    kw: dict[str, typing.Any]


class ConfigFileContents(BaseModel):
    data: str


class ConfigFileName(BaseModel):
    path: str
