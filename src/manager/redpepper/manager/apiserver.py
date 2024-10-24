import io
import logging
import os
import pathlib
import secrets
import time
import typing

import argon2
import hpack.hpack
import hpack.table
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

from .config import APIConfig

logger = logging.getLogger(__name__)

# Silence hpack logging
hpack.hpack.log.setLevel(logging.WARNING)
hpack.table.log.setLevel(logging.WARNING)

if typing.TYPE_CHECKING:
    from .manager import Manager


class APIServer:
    def __init__(self, manager: "Manager", config: APIConfig):
        self.manager = manager
        self.file_manager = FileManager(config.data_base_dir)
        self.config = config
        self.app = FastAPI()
        self.app.add_api_route(
            "/api/v1/agents",
            self.get_agents,  # type: ignore
        )
        self.app.add_api_route(
            "/api/v1/agents/names",
            self.get_agent_names,  # type: ignore
        )
        self.app.add_api_route(
            "/api/v1/agents/connected",
            self.get_connected_agents,  # type: ignore
        )
        self.app.add_api_route(
            "/api/v1/config/file",
            self.get_config_file,  # type: ignore
        )
        self.app.add_api_route(
            "/api/v1/config/file",
            self.save_config_file,  # type: ignore
            methods=["POST"],
        )
        self.app.add_api_route(
            "/api/v1/config/file",
            self.delete_config_file,  # type: ignore
            methods=["DELETE"],
        )
        self.app.add_api_route(
            "/api/v1/config/file",
            self.rename_config_file,  # type: ignore
            methods=["PATCH"],
        )
        self.app.add_api_route(
            "/api/v1/config/file",
            self.create_config_file,  # type: ignore
            methods=["PUT"],
        )
        self.app.add_api_route(
            "/api/v1/config/tree",
            self.get_config_tree,  # type: ignore
        )
        self.app.add_api_route(
            "/api/v1/command",
            self.command,  # type: ignore
            methods=["POST"],
        )
        self.app.add_api_route(
            "/api/v1/commands/last",
            self.get_command_log_last,  # type: ignore
        )
        self.app.add_api_websocket_route(
            "/api/v1/events/ws",
            self.event_channel,
        )
        self.app.add_api_route(
            "/api/v1/login",
            self.login,  # type: ignore
            methods=["POST"],
        )
        self.app.add_api_route(
            "/api/v1/logout",
            self.logout,  # type: ignore
            methods=["POST"],
        )
        self.app.add_api_route(
            "/api/v1/verify_totp",
            self.verify_totp,  # type: ignore
            methods=["POST"],
        )
        self.app.add_api_route(
            "/api/v1/totp_qr",
            self.get_totp_qr,
        )
        if config.api_static_dir:
            self.app.mount("/", StaticFiles(directory=config.api_static_dir, html=True))
        self.app.add_middleware(CORSMiddleware)
        if not config.api_session_secret_key.get_secret_value():
            raise ValueError("api_session_secret_key is an empty string")
        self.app.add_middleware(
            SessionMiddleware,
            secret_key=config.api_session_secret_key.get_secret_value(),
            https_only=True,
            max_age=self.config.api_session_max_age,
            same_site="strict",
        )
        self.hconfig = hypercorn.Config()
        self.hconfig.loglevel = "INFO"
        self.hconfig.bind = [f"{self.config.api_bind_host}:{self.config.api_bind_port}"]
        self.hconfig.certfile = str(self.config.api_tls_cert_file)
        if (
            not self.config.api_tls_key_file_allow_insecure
            and os.stat(self.config.api_tls_key_file).st_mode & 0o77 != 0
        ):
            raise ValueError(
                "TLS key file %s is insecure, please set permissions to 600"
                % self.config.api_tls_key_file,
            )
        self.hconfig.keyfile = str(self.config.api_tls_key_file)
        if self.config.api_tls_key_password:
            self.hconfig.keyfile_password = (
                self.config.api_tls_key_password.get_secret_value()
            )

    async def run(self):
        logger.debug("Starting API server")
        self.shutdown_event = trio.Event()
        await serve(
            self.app,  # type: ignore
            self.hconfig,
            shutdown_trigger=self.shutdown_event.wait,
        )
        logger.debug("API server stopped")

    async def shutdown(self):
        logger.info("Shutting down API server")
        self.shutdown_event.set()

    def get_auth_for_user(self, username):
        logins = self.config.api_logins
        for login in logins:
            if login.username == username:
                return login
        return None

    def check_credentials(self, username, password):
        logger.info("Checking credentials for user %s", username)
        starttime = time.monotonic()
        success = False
        login = self.get_auth_for_user(username)
        if login and argon2.PasswordHasher().verify(login.password_hash, password):
            success = True
        else:
            logger.warning("Login failed for user %s", username)
        endtime = time.monotonic()
        # Add a constant time delay to make timing attacks harder
        CONSTANT_TIME = 0.5
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
        if login and login.totp_secret:
            return pyotp.TOTP(
                login.totp_secret.get_secret_value(),
                name=username,
                issuer="RedPepper API",
            ).verify(otp)
        logger.debug("No TOTP secret found for user %s", username)
        return False

    def get_totp_qr_data(self, username):
        logger.debug("Generating TOTP QR code for user %s", username)
        try:
            import qrcode
        except ImportError:
            return None
        login = self.get_auth_for_user(username)
        if login and login.totp_secret:
            uri = pyotp.TOTP(
                login.totp_secret.get_secret_value(),
                name=username,
                issuer="RedPepper API",
            ).provisioning_uri()
            qr = qrcode.make(uri)
            stream = io.BytesIO()
            qr.save(stream, "PNG")
            return stream.getvalue()
        logger.debug("No TOTP secret found for user %s", username)
        return False

    # API Endpoints

    async def event_channel(self, websocket: WebSocket):
        try:
            self.check_session(websocket)
        except HTTPException:
            raise WebSocketException(status.WS_1008_POLICY_VIOLATION)
        consumer = self.manager.event_bus.add_consumer()
        try:
            await websocket.accept()
            async for event in consumer:
                await websocket.send_json(event)
        finally:
            self.manager.event_bus.remove_consumer(consumer)

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
        except Exception:
            logger.error("Error sending command", exc_info=True)
            return {"success": False, "detail": "internal error"}
        return {"success": True}

    async def create_config_file(
        self, request: Request, path: str, isdir: bool = False
    ):
        self.check_session(request)
        func = self.file_manager.create_new_conf_file
        if isdir:
            func = self.file_manager.create_new_conf_dir
        success, detail = await trio.to_thread.run_sync(func, path)
        return {"success": success, "detail": detail}

    async def delete_config_file(self, request: Request, path: str):
        self.check_session(request)
        success, detail = await trio.to_thread.run_sync(
            self.file_manager.delete_conf_file, path
        )
        return {"success": success, "detail": detail}

    async def get_agents(self, request: Request):
        self.check_session(request)
        agents = []
        connected = self.manager.connected_agents()
        for agent in self.manager.data_manager.get_agent_names():
            agents.append(
                {
                    "id": agent,
                    "connected": agent in connected,
                }
            )
        return {"agents": agents}

    async def get_agent_names(self, request: Request):
        self.check_session(request)
        return {"agents": self.manager.data_manager.get_agent_names()}

    async def get_config_file(self, request: Request, path: str):
        self.check_session(request)
        success, data = await trio.to_thread.run_sync(
            self.file_manager.get_conf_file, path
        )
        return {"success": success, "content": data}

    async def get_config_tree(self, request: Request):
        self.check_session(request)
        tree = await trio.to_thread.run_sync(self.file_manager.get_conf_file_tree)
        return {"tree": tree}

    async def get_connected_agents(self, request: Request):
        self.check_session(request)
        return {"agents": self.manager.connected_agents()}

    async def get_command_log_last(self, request: Request, max: int = 20):
        self.check_session(request)
        return {
            "commands": [
                command async for command in self.manager.command_log.last(max)
            ]
        }

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
            self.file_manager.rename_conf_file, path, new_path.path
        )
        return {"success": success, "detail": detail}

    async def save_config_file(
        self, request: Request, path: str, data: "ConfigFileContents"
    ):
        self.check_session(request)
        success, detail = await trio.to_thread.run_sync(
            self.file_manager.save_conf_file, path, data.data
        )
        return {"success": success, "detail": detail}

    async def verify_totp(self, request: Request, totp: "TOTPCredentials"):
        username = request.session.get("username", None)
        if not username:
            return {"success": False, "detail": "not logged in"}
        if self.check_totp(username, totp.totp):
            request.session["otp_verified"] = True
            return {"success": True}
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


class FileManager:
    def __init__(self, base_path: pathlib.Path):
        self.base_path = base_path

    def get_full_path(self, path: str) -> str:
        parts = []
        for part in path.split("/"):
            if not part:
                continue
            if part.startswith(".") or "\\" in part:
                raise ValueError("Invalid path")
            parts.append(part)
        return os.path.join(self.base_path, *parts)

    def get_conf_file(self, path: str) -> tuple[bool, str]:
        try:
            full_path = self.get_full_path(path)
        except ValueError as e:
            return False, str(e)
        try:
            with open(full_path, "r") as f:
                data = f.read()
        except FileNotFoundError:
            return False, "File does not exist"
        except IsADirectoryError:
            return False, "Path is a directory"
        except PermissionError:
            return False, "Permission denied"
        except UnicodeDecodeError:
            return False, "File is not a text file"
        return True, data

    def save_conf_file(self, path: str, data: str):
        try:
            full_path = self.get_full_path(path)
        except ValueError as e:
            return False, str(e)
        try:
            with open(full_path, "w") as f:
                f.write(data)
        except FileNotFoundError:
            return False, "Parent directory does not exist"
        except IsADirectoryError:
            return False, "Path is a directory"
        except PermissionError:
            return False, "Permission denied"
        return True, ""

    def delete_conf_file(self, path: str):
        try:
            full_path = self.get_full_path(path)
        except ValueError as e:
            return False, str(e)
        try:
            if os.path.isdir(full_path):
                os.rmdir(full_path)
            else:
                os.remove(full_path)
        except FileNotFoundError:
            return False, "File does not exist"
        except PermissionError:
            return False, "Permission denied"
        except OSError:
            return False, "Folder is not empty"
        return True, ""

    def create_new_conf_file(self, path: str):
        try:
            full_path = self.get_full_path(path)
        except ValueError as e:
            return False, str(e)
        try:
            with open(full_path, "x"):
                pass
        except FileExistsError:
            return False, "File already exists"
        except FileNotFoundError:
            return False, "Parent directory does not exist"
        except PermissionError:
            return False, "Permission denied"
        return True, ""

    def create_new_conf_dir(self, path: str):
        try:
            full_path = self.get_full_path(path)
        except ValueError as e:
            return False, str(e)
        try:
            os.mkdir(full_path)
        except FileExistsError:
            return False, "Directory already exists"
        except FileNotFoundError:
            return False, "Parent directory does not exist"
        except PermissionError:
            return False, "Permission denied"
        return True, ""

    def rename_conf_file(self, path: str, new_path: str):
        try:
            full_path = self.get_full_path(path)
            new_full_path = self.get_full_path(new_path)
        except ValueError as e:
            return False, str(e)
        try:
            if os.path.exists(new_full_path):
                return False, "Destination path already exists"
            os.replace(full_path, new_full_path)
        except FileNotFoundError:
            return False, "File does not exist"
        except PermissionError:
            return False, "Permission denied"
        return True, ""

    def get_conf_file_tree(self):
        node = self._get_node(self.base_path, "")
        return node.get("children", [])

    def _get_node(self, base, name):
        node = {"name": name}
        path = os.path.join(base, name)
        if os.path.isdir(path):
            node["children"] = [
                self._get_node(path, name)
                for name in os.listdir(path)
                if not name.startswith(".") and "\\" not in name
            ]
            node["children"].sort(key=lambda x: ("children" not in x, x["name"]))
        return node
