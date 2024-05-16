import functools
import logging
import os
import re

import ordered_set
import yaml

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=256)
def translate_wildcard_pattern(pattern):
    return re.compile(
        pattern.replace(".", r"\.").replace("*", r".*").replace("?", r".")
    )


NODATA = object()


class DataManager:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self._loaded_yaml_files = {}

    def get_data(self, requester_id, name):
        groups = self.get_groups(requester_id)
        for group in reversed(groups):
            gdata = self.get_group_data(group, name)
            if gdata is not NODATA:
                return gdata
        return NODATA

    def get_state(self, requester_id):
        groups = self.get_groups(requester_id)
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

    def get_groups(self, requester_id):
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
                if not pattern.fullmatch(requester_id):
                    continue
                if not isinstance(grouplist, list):
                    logger.warn("Group data for %s is not a list", pattern)
                    continue
            elif requester_id != pattern:
                continue
            for group in grouplist:
                if not isinstance(group, str):
                    logger.warn("Group is not a string: %r", group)
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
        if not os.path.exists(path):
            logger.warn("File not found: %s", path)
            if path in self._loaded_yaml_files:
                del self._loaded_yaml_files[path]
            return {}
        if path in self._loaded_yaml_files:
            mtime, data = self._loaded_yaml_files[path]
            if mtime == os.path.getmtime(path):
                return data
        with open(path) as f:
            data = yaml.safe_load(f)
        self._loaded_yaml_files[path] = (os.path.getmtime(path), data)
        return data
