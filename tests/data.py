import shutil
from pathlib import Path

import yaml

DEFAULT_DATA_DIR = Path(__file__).parent / ".test-data"
_MANAGER: "TestDataManager | None" = None


class _YAMLSaver(dict):
    def __init__(self, file: Path, init: dict):
        self.file = file
        super().__init__(init)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        with open(self.file, "w") as stream:
            yaml.safe_dump(dict(self), stream)


class TestDataManager:
    """Manages the data directory for tests"""

    def __init__(self, data_dir: Path = DEFAULT_DATA_DIR):
        self.data_dir = data_dir
        self.ensure_data_dir()

    def ensure_data_dir(self) -> None:
        """Ensure that the data directory exists, creating it if necessary"""
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True)

    def clean(self) -> None:
        """Clean the data directory"""
        for item in self.data_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    def yamlfile(self, file: Path, ignore_missing=True) -> _YAMLSaver:
        """Load a YAML file from the data directory a"""
        try:
            with open(file, "r") as stream:
                source = yaml.safe_load(stream)
        except FileNotFoundError:
            if not ignore_missing:
                raise
            source = {}
        return _YAMLSaver(file, source)

    def setup_agent(
        self,
        agent_id: str,
        agent_secret: str,
        allowed_ips: list[str] | str | None = None,
    ):
        import hashlib

        with self.yamlfile(self.data_dir / "agents.yml") as agents_yml:
            agents_yml[agent_id] = {
                "secret_hash": hashlib.sha256(agent_secret.encode()).hexdigest(),
                "allowed_ips": allowed_ips,
            }


def get_data_manager() -> TestDataManager:
    global _MANAGER
    if _MANAGER is None:
        _MANAGER = TestDataManager()
    return _MANAGER
