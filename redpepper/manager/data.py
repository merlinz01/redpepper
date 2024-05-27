import functools
import ipaddress
import logging
import os
import re

import atomicwrites
import ordered_set
import yaml

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=256)
def translate_wildcard_pattern(pattern):
    return re.compile(
        pattern.replace(".", r"\.").replace("*", r".*").replace("?", r".")
    )


NODATA = object()
DEFAULT_AUTH = {
    "fingerprint": None,
    "secret": None,
    "allowed_ips": [],
}


class DataManager:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self._loaded_yaml_files = {}

    def get_auth(self, agent_id):
        agents_yml = self.load_yaml_file(os.path.join(self.base_dir, "agents.yml"))
        if not isinstance(agents_yml, dict):
            logger.warn("agents.yml is not a dict")
            return DEFAULT_AUTH
        auth: dict = agents_yml.get(agent_id, None)
        if auth is None:
            logger.warn("No auth data for %s", agent_id)
            return DEFAULT_AUTH
        if not isinstance(auth, dict):
            logger.warn("Auth data for %s is not a dict", agent_id)
            return DEFAULT_AUTH
        auth = auth.copy()
        f = auth.setdefault("cert_hash", "")
        if not isinstance(f, str):
            logger.warn("Cert hash for %s is not a string", agent_id)
            auth["cert_hash"] = None
        s = auth.setdefault("secret_hash", "")
        if not isinstance(s, str):
            logger.warn("Secret hash for %s is not a string", agent_id)
            auth["secret_hash"] = None
        allowed_ips = auth.setdefault("allowed_ips", [])
        if isinstance(allowed_ips, str):
            auth["allowed_ips"] = allowed_ips = [allowed_ips]
        if not isinstance(allowed_ips, list):
            logger.warn("Allowed IPs for %s is not a list", agent_id)
            auth["allowed_ips"] = []
        if not auth["allowed_ips"]:
            logger.warn("Allowed IPs for %s is empty", agent_id)
        allowed_ips = []
        for ip in auth["allowed_ips"]:
            if not isinstance(ip, str):
                logger.warn("Allowed IP range %r is not a string", agent_id)
                continue
            try:
                allowed_ips.append(ipaddress.ip_network(ip))
            except ValueError:
                logger.warn("Invalid IP range %r for %s", ip, agent_id)
        auth["allowed_ips"] = allowed_ips
        return auth

    def get_data(self, agent_id, name):
        data = self.get_custom_data(agent_id, name)
        if data is not NODATA:
            return data
        groups = self.get_groups(agent_id)
        for group in reversed(groups):
            gdata = self.get_group_data(group, name)
            if gdata is not NODATA:
                return gdata
        return NODATA

    def get_custom_data(self, agent_id, name):
        agents_yml = self.load_yaml_file(os.path.join(self.base_dir, "agents.yml"))
        if not isinstance(agents_yml, dict):
            logger.warn("agents.yml is not a dict")
            return NODATA
        obj = agents_yml.get(agent_id, None)
        if not obj:
            logger.warn("No agent data for %s", agent_id)
            return NODATA
        obj = obj.get("data", {})
        for key in name.split("."):
            if not isinstance(obj, dict):
                break
            obj = obj.get(key, NODATA)
            if obj is NODATA:
                break
        return obj

    def get_file_path(self, agent_id, name):
        # Sanitize the requested file name
        if name.startswith("/"):
            # Disallow absolute paths
            logger.debug("Requested file name starts with /: %r", name)
            return None
        parts = name.split("/")
        for part in parts:
            if not part:
                # Allow empty parts (double slashes, trailing slashes)
                continue
            if part.startswith(".") or "\\" in part:
                # Disallow ".", "..", hidden files, and backslashes
                logger.debug("Requested file name contains invalid part: %r", name)
                return None
        # Look for the requested file in the agent's groups
        groups = self.get_groups(agent_id)
        for group in reversed(groups):
            path = os.path.join(self.base_dir, "data", group, *parts)
            if os.path.isfile(path):
                logger.debug("Found requested file in group %s: %r", group, name)
                return path
        logger.debug("Requested file not found: %r", name)
        return None

    def get_state(self, agent_id):
        groups = self.get_groups(agent_id)
        state = {}
        for group in groups:
            group_data = self.load_yaml_file(
                os.path.join(self.base_dir, "state", f"{group}.yml")
            )
            if not isinstance(group_data, dict):
                logger.warn("Group data for %s is not a dict", group)
                continue
            for key, value in group_data.items():
                if key in state:
                    logger.warn("Duplicate key %s in group %s", key, group)
                state[key] = value
        return state

    def get_groups(self, agent_id):
        groups = ordered_set.OrderedSet()
        groups_yml: dict = self.load_yaml_file(
            os.path.join(self.base_dir, "groups.yml")
        )
        if not isinstance(groups_yml, dict):
            logger.warn("groups.yml is not a dict")
            return groups
        for pattern, grouplist in groups_yml.items():
            if "*" in pattern:
                pattern = translate_wildcard_pattern(pattern)
                if not pattern.fullmatch(agent_id):
                    continue
                if not isinstance(grouplist, list):
                    logger.warn("Group data for pattern %s is not a list", pattern)
                    continue
            elif agent_id != pattern:
                continue
            for group in grouplist:
                if not isinstance(group, str):
                    logger.warn("Group name is not a string: %r", group)
                    continue
                if "/" in group or "\\" in group or group == "..":
                    logger.warn("Group name contains invalid character: %r", group)
                    continue
                groups.add(group)
        return groups

    def get_group_data(self, group, name):
        group_data = self.load_yaml_file(
            os.path.join(self.base_dir, "data", f"{group}.yml")
        )
        obj = group_data
        for key in name.split("."):
            if not isinstance(obj, dict):
                return NODATA
            obj = obj.get(key, NODATA)
            if obj is NODATA:
                return NODATA
        return obj

    def load_yaml_file(self, path):
        mtime, data = self._loaded_yaml_files.get(path, (None, None))
        if mtime:
            try:
                if mtime == os.path.getmtime(path):
                    logger.debug("Using cached data for %s", path)
                    return data
            except FileNotFoundError:
                logger.warn("File not found: %s", path)
                self._loaded_yaml_files.pop(path, None)
                return {}
        try:
            logger.debug("Loading data from %s", path)
            with open(path) as f:
                data = yaml.safe_load(f)
                self._loaded_yaml_files[path] = (os.path.getmtime(path), data)
        except FileNotFoundError:
            logger.warn("File not found: %s", path)
            self._loaded_yaml_files.pop(path, None)
        return data

    def get_custom_state_module(self, module_name):
        if not module_name.isidentifier():
            logger.warn("Invalid module name: %r", module_name)
            return None
        path = os.path.join(self.base_dir, "custom-states", module_name + ".py")
        if not os.path.isfile(path):
            logger.debug("Module file not found: %r", path)
            return None
        try:
            with open(path) as f:
                return f.read()
        except Exception as e:
            logger.warn("Failed to read module file: %r", path, exc_info=e)
            return None

    def get_agents(self):
        agents_yml = self.load_yaml_file(os.path.join(self.base_dir, "agents.yml"))
        if not isinstance(agents_yml, dict):
            logger.warn("agents.yml is not a dict")
            return []
        return list(agents_yml.keys())

    def get_conf_file(self, path):
        for p in path:
            if p.startswith(".") or "/" in p or "\\" in p:
                return None
        path = os.path.join(self.base_dir, *path)
        try:
            with open(path) as f:
                return f.read()
        except Exception as e:
            logger.warn("Failed to read file: %r", path, exc_info=e)
            return None

    def save_conf_file(self, path, data):
        for p in path:
            if p.startswith(".") or "/" in p or "\\" in p:
                return False
        path = os.path.join(self.base_dir, *path)
        try:
            with atomicwrites.AtomicWriter(path, "w", overwrite=True).open() as f:
                f.write(data)
            return True
        except Exception as e:
            logger.warn("Failed to write file: %r", path, exc_info=e)
            return False

    def get_conf_file_tree(self):
        node = self._get_node(self.base_dir, "")
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
