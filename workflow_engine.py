import asyncio
import inspect
import logging
from typing import Callable, Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WorkflowEngine")


class WorkflowTask:
    def __init__(self, name: str, func: Callable, dependencies: List[str] = None):
        self.name = name
        self.func = func
        self.dependencies = dependencies or []
        self.status = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED


class AsyncWorkflowEngine:
    def __init__(self):
        self.tasks: Dict[str, WorkflowTask] = {}

    def add_task(self, name: str, func: Callable, dependencies: List[str] = None):
        if name in self.tasks:
            raise ValueError(f"Task '{name}' already exists.")
        self.tasks[name] = WorkflowTask(name, func, dependencies)

    def _validate_dependencies(self):
        visited = set()
        visiting = set()

        def visit(task_name: str):
            if task_name in visiting:
                raise ValueError(f"Circular dependency detected involving '{task_name}'.")
            if task_name in visited:
                return

            visiting.add(task_name)
            task = self.tasks.get(task_name)
            if task is None:
                raise KeyError(f"Task '{task_name}' does not exist.")

            for dependency in task.dependencies:
                if dependency not in self.tasks:
                    raise KeyError(
                        f"Task '{task_name}' depends on missing task '{dependency}'."
                    )
                visit(dependency)

            visiting.remove(task_name)
            visited.add(task_name)

        for task_name in self.tasks:
            visit(task_name)

    async def _wait_for_dependencies(self, task_name: str):
        task = self.tasks[task_name]

        while True:
            pending = []
            for dependency in task.dependencies:
                dependency_task = self.tasks[dependency]
                if dependency_task.status == "FAILED":
                    task.status = "FAILED"
                    raise RuntimeError(
                        f"Dependency {dependency} failed. Aborting {task_name}."
                    )
                if dependency_task.status != "COMPLETED":
                    pending.append(dependency)

            if not pending:
                return

            await asyncio.sleep(0.01)

    async def _execute_task(self, task_name: str, context: Dict[str, Any]):
        task = self.tasks[task_name]
        await self._wait_for_dependencies(task_name)

        task.status = "RUNNING"
        logger.info(f"Starting execution of task: {task_name}")

        try:
            if asyncio.iscoroutinefunction(task.func):
                await task.func(context)
            else:
                result = task.func(context)
                if inspect.isawaitable(result):
                    await result

            task.status = "COMPLETED"
            logger.info(f"Successfully completed task: {task_name}")
        except Exception as exc:
            task.status = "FAILED"
            logger.error(f"Task {task_name} failed with error: {str(exc)}")
            raise

    async def run_workflow(self, initial_context: Dict[str, Any] = None):
        self._validate_dependencies()
        context = dict(initial_context or {})
        logger.info("Initiating workflow execution pipeline...")

        execution_futures = [
            asyncio.create_task(self._execute_task(task_name, context))
            for task_name in self.tasks
        ]

        results = await asyncio.gather(*execution_futures, return_exceptions=True)
        logger.info("Workflow execution cycle completed.")
        return results