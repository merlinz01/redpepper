import functools
import importlib.util
import logging
import os
import pathlib
import re
from types import ModuleType
from typing import Any

import yaml
from ordered_set import OrderedSet

logger = logging.getLogger(__name__)
VALID_ID = re.compile(r"^[a-zA-Z0-9_-]+$")  # only alphanumeric, dash, and underscore


@functools.lru_cache(maxsize=256)
def translate_wildcard_pattern(pattern: str):
    return re.compile(
        pattern.replace(".", r"\.").replace("*", r".*").replace("?", r".")
    )


def is_valid_id(id):
    return isinstance(id, str) and bool(VALID_ID.match(id))


class DataManager:
    def __init__(self, base_dir: pathlib.Path):
        self.base_dir = base_dir
        self._loaded_yaml_files = {}
        self._loaded_request_modules = {}

    def load_yaml_file(self, path: str) -> Any:
        """Load a YAML file from the base directory, or return None if not found or invalid."""
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
            with open(os.path.join(self.base_dir, path)) as f:
                try:
                    data = yaml.safe_load(f)
                except yaml.YAMLError:
                    logger.warn("Failed to load YAML file: %r", path, exc_info=True)
                    data = None
                self._loaded_yaml_files[path] = (os.path.getmtime(path), data)
        except FileNotFoundError:
            self._loaded_yaml_files.pop(path, None)
        return data

    # Agents and groups

    def get_agent_names(self):
        """Get a list of agent IDs from agents.yml."""
        agents_yml = self.load_yaml_file("agents.yml") or {}
        if not isinstance(agents_yml, dict):
            logger.warn("agents.yml is not a mapping")
            return []
        return list(agents_yml.keys())

    def get_agent_entry(self, agent_id: str) -> dict:
        """Get the agent entry from agents.yml, or an empty dict if not found."""
        if not is_valid_id(agent_id):
            logger.warn("Invalid agent ID: %r", agent_id)
            return {}
        agents_yml = self.load_yaml_file("agents.yml") or {}
        if not isinstance(agents_yml, dict):
            logger.warn("agents.yml is not a mapping")
            return {}
        entry: dict = agents_yml.get(agent_id, {})
        if not isinstance(entry, dict):
            logger.warn("Agent entry for %s is not a mapping", agent_id)
            return {}
        return entry

    def get_groups_for_agent(self, agent_id: str) -> OrderedSet[str]:
        """Get the groups for the agent, based on groups.yml.
        Returns an ordered set of group IDs.
        The order is to be exactly the order in which each group is initially given to the agent.
        """
        groups: OrderedSet[str] = OrderedSet(())
        groups_yml: dict = self.load_yaml_file("groups.yml") or {}
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
                if not is_valid_id(group):
                    logger.warn("Invalid group ID: %r", group)
                    continue
                groups.add(group)
        return groups

    # Data

    def get_data_for_agent(self, agent_id: str, name: str) -> Any:
        """Get the data for the agent, based on the data definitions for the groups to which the agent belongs.
        The data is searched in reverse order of the groups, so that the data from the last group is used first.
        Data defined under the "group" key of the agent entry gets highest priority.
        The name is a dot-separated path to the desired data.
        Special names:
        "<agent_id>" returns the agent ID.
        "<groups>" returns the list of groups to which the agent belongs.
        """
        if name == "<agent_id>":
            return agent_id
        elif name == "<groups>":
            return list(self.get_groups_for_agent(agent_id))
        try:
            return self.get_data_from_mapping(
                self.get_agent_entry(agent_id).get("data", {}), name
            )
        except KeyError:
            pass
        for group_id in reversed(self.get_groups_for_agent(agent_id)):
            try:
                return self.get_data_for_group(group_id, name)
            except KeyError:
                pass
        raise KeyError(f"data {name!r} not defined for {agent_id}")

    def get_data_for_group(self, group: str, name: str):
        """Get the data for the group from the data directory, or raise KeyError if not found."""
        group_data = self.load_yaml_file(f"data/{group}.yml") or {}
        return self.get_data_from_mapping(group_data, name)

    def get_data_from_mapping(self, mapping: dict, name: str) -> Any:
        """Get a value from a nested mapping using a dot-separated path, or raise KeyError if not found."""
        obj = mapping
        for key in name.split("."):
            if not isinstance(obj, dict):
                raise KeyError(f"key {key!r} not found")
            obj = obj[key]
        return obj

    def get_data_file_path(self, agent_id: str, name: str) -> str:
        """Get the full path for the requested file name as allowed by the agent's groups."""
        # Sanitize the requested file name
        parts = []
        for part in name.split("/"):
            if not part:
                # Allow empty parts (double slashes, leading/trailing slashes)
                continue
            if part.startswith(".") or "\\" in part:
                # Disallow ".", "..", hidden files, and backslashes
                raise ValueError(f"Unacceptable file name: {name!r}")
            parts.append(part)
        # Look for the requested file in the agent's groups
        groups = self.get_groups_for_agent(agent_id)
        for group in reversed(groups):
            path = os.path.join(self.base_dir, "data", group, *parts)
            if os.path.isfile(path):
                logger.debug("Found requested file in group %s: %r", group, name)
                return path
        raise FileNotFoundError(f"File not found: {name}")

    # State definitions

    def get_state_definition_for_agent(
        self, agent_id: str, state_id: str | None = None
    ) -> dict:
        """Get the state definition for the agent, based on the state definitions for the groups to which the agent belongs.
        The state definitions are merged in the order of the groups, so that the state from the last group is used first.
        This is so that parts of a state definition can be overridden for a specific agent.

        The state_id can be used to load state definitions from "state/{group}/{state_id}.yml".
        """
        groups = self.get_groups_for_agent(agent_id)
        if state_id:
            if not is_valid_id(state_id):
                raise ValueError(f"Invalid state name: {state_id!r}")
            path = "state/{group}/{state_id}.yml"
        else:
            path = "state/{group}.yml"
        state = {}
        for group in groups:
            group_data = (
                self.load_yaml_file(path.format(group=group, state_id=state_id)) or {}
            )
            if not isinstance(group_data, dict):
                logger.warn("Group data for %s is not a dict", group)
                continue
            state.update(group_data)
        try:
            state = self.interpolate_value_for_agent(agent_id, state)
        except KeyError as e:
            raise ValueError(f"Interpolation failed for state definition: {e}")
        return state

    INTERPOLATION_REGEX = re.compile(r"\${((([^{]+)})|{)")
    FULL_INTERPOLATION_REGEX = re.compile(r"^\${([^{]+)}$")

    def interpolate_value_for_agent(self, agent_id: str, value: Any) -> Any:
        """Interpolate the value using the data for the agent."""
        if isinstance(value, dict):
            new = {}
            for k, v in value.items():
                new[k] = self.interpolate_value_for_agent(agent_id, v)
            return new
        elif isinstance(value, list):
            new = []
            for v in value:
                new.append(self.interpolate_value_for_agent(agent_id, v))
            return new
        elif isinstance(value, str):
            # If the whole thing is an interpolation, return the result directly
            # so that structured data can be used as-is
            if self.FULL_INTERPOLATION_REGEX.match(value):
                return self.get_data_for_agent(agent_id, value[2:-1])

            def repl(m: re.Match):
                if m.group(1) == "{":
                    return "${"
                return str(self.get_data_for_agent(agent_id, m.group(3)))

            return self.INTERPOLATION_REGEX.sub(repl, value)
        return value

    # Custom operation modules

    def get_operation_module_path(self, module_name: str):
        if not module_name.isidentifier():
            raise ValueError(f"Invalid module name: {module_name!r}")
        path = os.path.join(self.base_dir, "operations", module_name + ".py")
        return path

    # Custom request modules

    def get_request_module(self, agent_id: str, module_name: str) -> ModuleType:
        if not module_name.isidentifier():
            raise ImportError(f"Invalid request module name: {module_name!r}")
        key = (agent_id, module_name)
        for group_id in reversed(self.get_groups_for_agent(agent_id)):
            path = os.path.join(
                self.base_dir, "requests", group_id, module_name + ".py"
            )
            if os.path.isfile(path):
                break
        else:
            raise ImportError(f"Request module not found: {module_name!r}")
        try:
            module, cpath, cmtime, csize = self._loaded_request_modules[key]
            if path != cpath:
                raise KeyError
            stat = os.stat(path)
            mtime = stat.st_mtime
            if mtime != cmtime:
                raise KeyError
            size = stat.st_size
            if size != csize:
                raise KeyError
            return module
        except KeyError:
            stat = os.stat(path)
            mtime = stat.st_mtime
            size = stat.st_size
            try:
                spec = importlib.util.spec_from_file_location(
                    "redpepper.requests." + module_name, path
                )
                if spec is None or spec.loader is None:
                    raise ImportError(f"Error loading request module {module_name!r}")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self._loaded_request_modules[key] = (module, path, mtime, size)
                return module
            except Exception as e:
                logger.error("Error loading request module: %r", path, exc_info=True)
                self._loaded_request_modules.pop(key, None)
                raise ImportError(
                    f"Error loading request module {module_name!r}"
                ) from e
