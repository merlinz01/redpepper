
# Data

"Data" in this context refers to data, intended to be distributed to agents, stored in the manager's configuration directory.

An agent can only access data for the groups to which it belongs.

Data for a group is defined in a YAML file with the group's name in the `data` directory.
Any data you wish for the agent to be able to access can be defined in these files (passwords etc.).
You can also put files you wish for the agent to access in a subdirectory of `data` with the group's name.

Any data defined in any group is overridden by state or data with the same name in subsequently defined groups.

Data is served to agents upon request.
