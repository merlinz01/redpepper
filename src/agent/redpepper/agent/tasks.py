class Task:
    def __init__(self, name, data=None, dependencies=None):
        self.name: str = name
        self.data = data
        self.dependencies: set[str] = dependencies or set()
        for d in self.dependencies:
            if not isinstance(d, str):
                raise TypeError(f"Dependency {d} is not a string")

    def __str__(self):
        return f"Task({self.name})"


def topological_sort(tasks: dict[str, Task]):
    sorted_tasks = []
    tasks_left = list(tasks.values())

    while tasks_left:
        # Find a task with no dependencies
        for t in tasks_left:
            if not t.dependencies:
                task = t
                tasks_left.remove(t)
                break
        else:
            raise ValueError("A cycle is detected or some tasks are not reachable.")
        for t in tasks_left:
            if task.name in t.dependencies:
                t.dependencies.remove(task.name)
        sorted_tasks.append(task)

    return sorted_tasks
