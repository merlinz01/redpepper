### States

A "state" in the context of RedPepper is a definition of any number of operations that put an agent's machine into a desired state.

States are analogous to [Salt](https://github.com/saltstack/salt) states.

All state configuration is in YAML files in the `state` subdirectory of the config directory.
See the `config/data/state` directory for more examples.

An agent can only access states for the groups to which it belongs.

States for a group are defined in a YAML file with the group's name in the `data` directory.
Any state defined for any group is overridden by a state with the same name in subsequently defined groups.

These are mappings with various parameters,
most importantly a `type` parameter which specifies name of the operation to perform
and determines the allowed other parameters.

States can also be defined as an array of states (a state group) which is executed as a unit in the order defined.
This is useful for a closely-related group of operations which must be performed in a specific order.

All states can have a `if` parameter which defines a condition
which if false prevents the state from being ensured.
Most operations, however, have an already-defined test
which prevents unneeded operations if the state already exists.
A notable exception is the `command.Run` operation
which can serve as the basis for ad-hoc states without defining operation modules.

A special condition usable in the `if` parameter is the `changed` condition
which allows a state to be executed only if a previous state changed something.
This is useful for things like build steps which should only be executed if a previous step changed the source.
