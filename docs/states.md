### States

A "state" in the context of RedPepper is a definition of any number of operations that put an agent's machine into a desired state.

States are analogous to [Salt](https://github.com/saltstack/salt) states.

All state configuration is in YAML files in the `state` subdirectory of the config directory.
See the `example-conf/state` directory for more examples.

An agent can only access states for the groups to which it belongs.

States for a group are defined in a YAML file with the group's name in the `data` directory.
Any state defined for any group is overridden by a state with the same name in subsequently defined groups.

These are mappings with various parameters,
most importantly a `type` parameter which specifies name of the operation to perform
and determines the allowed other parameters.

All states can have a `if` parameter which defines a condition
which if false prevents the state from being ensured.
Most operations, however, have an already-defined test
which prevents unneeded operations if the state already exists.
The notable exception is the `command.Run` operation
which can serve as the basis for ad-hoc states without defining operation modules.

States can have a `require` parameter which defines a list of the names
of other states which must be executed before it.
Circular dependencies in requirements will fail the entire state execution.
