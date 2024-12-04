import yaml

from redpepper.manager.data import DataManager
from tests.data import get_data_manager


def test_load_single_state():
    datamanager = get_data_manager()
    with datamanager.file("data/state/group1.yml") as f:
        f.write("""
- One:
    - Two:
        - Three:
            type: test.three
        - Four:
            type: test.four
- Five:
    type: test.five
""")
    with datamanager.yamlfile("data/agent.yml") as d:
        d["test1"] = {}
    with datamanager.yamlfile("data/groups.yml") as d:
        d["test1"] = ["group1"]
    d = DataManager(datamanager.path / "data")
    state = d.get_state_definition_for_agent("test1")
    assert state == [
        {
            "One": [
                {
                    "Two": [
                        {"Three": {"type": "test.three"}},
                        {"Four": {"type": "test.four"}},
                    ]
                }
            ]
        },
        {"Five": {"type": "test.five"}},
    ]


def test_merge_state():
    datamanager = get_data_manager()
    with datamanager.file("data/state/group1.yml") as f:
        f.write("""
- One:
    - Two:
        - Three:
            type: test.three
        - Four:
            type: test.four
- Five:
    type: test.five
- Ten:
    - Eleven:
        - Twelve:
            type: test.twelve
""")
    with datamanager.file("data/state/group2.yml") as f:
        f.write("""
- One:
    - Two:
        - Three:
            type: changed.three
- Five:
    - Six:
        - Seven:
            type: test.seven
""")
    with datamanager.file("data/state/group3.yml") as f:
        f.write("""
- One:
    - Eight:
        - Nine:
            type: test.nine
- Five:
    - Six:
        - Seven:
            type: changed.seven
- Ten:
    type: test.ten
""")
    with datamanager.yamlfile("data/agent.yml") as d:
        d["test1"] = {}
    with datamanager.yamlfile("data/groups.yml") as d:
        d["test1"] = ["group1", "group2", "group3"]
    d = DataManager(datamanager.path / "data")
    state = d.get_state_definition_for_agent("test1")
    combined = yaml.safe_load("""
- One:
    - Two:
        - Three:
            type: changed.three
        - Four:
            type: test.four
    - Eight:
        - Nine:
            type: test.nine
- Five:
    - Six:
        - Seven:
            type: changed.seven
- Ten:
    type: test.ten
""")
    assert state == combined
