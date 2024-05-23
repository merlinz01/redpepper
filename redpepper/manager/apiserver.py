import io
import logging
import secrets
import time

import hypercorn
import pyotp
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from hypercorn.trio import serve
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from trio import Event

logger = logging.getLogger(__name__)


class APIServer:
    def __init__(self, manager, config):
        self.manager = manager
        self.config = config
        self.app = FastAPI()
        self.app.add_api_route("/api/v1/agents", self.get_agents)
        self.app.add_api_route("/api/v1/agents/names", self.get_agent_names)
        self.app.add_api_route("/api/v1/agents/connected", self.get_connected_agents)
        self.app.add_api_route("/api/v1/login", self.login, methods=["POST"])
        self.app.add_api_route("/api/v1/logout", self.logout, methods=["POST"])
        self.app.add_api_route(
            "/api/v1/verify_totp", self.verify_totp, methods=["POST"]
        )
        self.app.add_api_route("/api/v1/totp_qr", self.get_totp_qr)
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["https://localhost:5173", "*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.app.add_middleware(
            SessionMiddleware,
            secret_key=config["api_session_secret_key"],
            https_only=True,
            max_age=self.config["api_session_max_age"],
        )
        self.hconfig = config = hypercorn.Config()
        self.hconfig.bind = [
            f"{self.config['api_bind_host']}:{self.config['api_bind_port']}"
        ]
        self.hconfig.certfile = self.config["api_tls_cert_file"]
        self.hconfig.keyfile = self.config["api_tls_key_file"]
        self.hconfig.keyfile_password = self.config["api_tls_key_password"]
        if not self.config["api_totp_secret"]:
            raise ValueError("api_totp_secret must be set in the configuration")
        if "changeme" in self.config["api_totp_secret"]:
            logger.error(
                "TOTP secret for API login is still set to a default value. This is insecure and must be changed."
            )
        if not self.config["api_session_secret_key"]:
            raise ValueError("api_session_secret_key must be set in the configuration")
        if "changeme" in self.config["api_session_secret_key"]:
            logger.error(
                "Session secret key for API login is still set to a default value. This is insecure and must be changed."
            )

    async def run(self):
        self.shutdown_event = Event()
        await serve(self.app, self.hconfig, shutdown_trigger=self.shutdown_event.wait)

    async def shutdown(self):
        logger.info("Shutting down API server")
        self.shutdown_event.set()

    def check_credentials(self, username, password):
        logger.info("Checking credentials for user %s", username)
        starttime = time.monotonic()
        success = False
        logins = self.config["api_logins"]
        if not isinstance(logins, list):
            logger.warn("API logins is not a list")
        else:
            for login in logins:
                if not isinstance(login, dict):
                    logger.warn("API login is not a dict")
                    continue
                if "username" not in login or "password" not in login:
                    logger.warn("API login is missing username or password")
                    continue
                if login["username"] == username and login["password"] == password:
                    logger.debug("Found valid login for user %s", username)
                    success = True
                    break
            else:
                logger.debug("No valid login found for user %s", username)
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
        return pyotp.TOTP(
            self.config["api_totp_secret"], name=username, issuer="RedPepper API"
        ).verify(otp)

    def get_totp_qr_data(self, username):
        logger.debug("Generating TOTP QR code for user %s", username)
        try:
            import qrcode
        except ImportError:
            return None
        uri = pyotp.TOTP(
            self.config["api_totp_secret"], name=username, issuer="RedPepper API"
        ).provisioning_uri()
        qr = qrcode.make(uri)
        stream = io.BytesIO()
        qr.save(stream, "PNG")
        return stream.getvalue()

    # API Endpoints

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

    async def get_connected_agents(self, request: Request):
        self.check_session(request)
        return {"agents": self.manager.connected_agents()}

    async def get_totp_qr(self, request: Request):
        self.check_session(request)
        return Response(
            content=self.get_totp_qr_data(request.session["username"]),
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
