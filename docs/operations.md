# Operations

An _operation_ is a procedure that can be performed on an agent's machine in order to produce a certain outcome.

Operations are analogous to [Salt](https://github.com/saltstack/salt) commands.

[States](states.md) are multiple operations which ensure an agent's machine is in a desired state.

## Defining operations

Operations are defined as subclasses of `redpepper.operations.Operation`.
These classes are stored in Python files as submodules of `redpepper.operations`.

You can define your own custom operation modules as Python files in the `operations` directory of the manager's agent-data directory.
These are automatically transmitted to and stored on agents' machines.

> All agents can access all operation modules, so don't put any secrets in your custom modules unless you are OK with all agents being able to access them.

> Because of the ability to define custom operations,
> the RedPepper project intends to limit the "built-in" operations
> to basic system administration utilities,
> rather than providing support for every operation under the sun,
> at least in this Git repository.
> If you define a specialized operation that you think could be useful to others,
> feel free to publish it in your own Github repository.

An operation can define the following methods:

### `def run(agent: Agent) -> Result`

This is where the operation really happens.

Generally the first thing to do in this method is to set up a Result object to store information about the operation's execution.

```python
result = Result()
```

If you need to run an external program frome this method,
do it like this:

```python
import subprocess
...
p = subprocess.run(
    ['/usr/bin/some-command', '--argument'],
    capture_output=True,
    text=True,
)
if not result.check_completed_process(p).succeeded:
    return result
```

This will update the result with the output of the command,
and set the success attribute to False.

If you know an operation might raise a Python error,
you can just not handle the error and it will be reported to the user.
However, sometimes we have some information (like previous process outputs)
that would be useful to report to the user along with the error traceback.
If that is the case, handle it like this:

```python
# Beforehand, result contains some useful information that we want the user to see whether or not the error occurrs.
try:
    # Some operation that "might" raise an error
    1 / 0
except ZeroDivisionError:
    # This retrieves exception information from sys.exc_info(),
    # adds the traceback to the output, and marks the result as failed.
    result.exception()
    return result
```

If you need to access [data](data.md) defined for the agent,
use the provided agent's `request_data()` method.

```python
ok, data = agent.request_data('some.key.defined.in.the.YAML.files')
```

### `def test(agent: Agent) -> bool`

This function is to determine if the operation needs to be executed,
or whether the desired outcome already exists.

Return True if the outcome already exists, or False if it does not and the command needs to be run.

By default this function returns False,
so that the operation's `run()` method is called every time.

### `def ensure(agent: Agent) -> Result`

Make sure the outcome exists by executing the operation if needed.

This function is basically a combination of `test()` and `run()`.
Most operations will not need to reimplement this method,
as the default implementation is sufficient.
