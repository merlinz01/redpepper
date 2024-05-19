### Statea

"State" in the context of RedPepper refers to a set of parameters describing a condition which may or may not be exist on an agent's machine, and parameters describing how to get it into that state.
For example, a `package.Installed` type of state describes a system package that the agent should make sure is installed.
States are analogous to those of [Salt](https://github.com/saltstack/salt).

All state configuration is in YAML files in the `state` subdirectory of the config directory.
See the `example/conf/state` directory for more examples.

An agent can only access states for the groups to which it belongs.

States for a group are defined in a YAML file with the group's name in the `data` directory.
These are mappings with various parameters, most importantly a `type` parameter which specifies the type of state and determines the allowed other parameters.
All states can have a `if` parameter which defines a condition which if false prevents the state from being ensured.

Any state or data defined in any group is overridden by state or data with the same name in subsequently defined groups.

State types are defined as Python classes in submodules of `pepper.states`.
You can put your own custom state modules in the `custom-states` subdirectory of the config directory.
All agents can access state modules, so don't put any secrets in them.
