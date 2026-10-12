import asyncio
import time
import uuid

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


app = FastAPI(
    title="NEXUS Distributed GPU",
    version="0.1.0",
    description="Coordenador experimental de tarefas distribuídas."
)

tasks: dict[str, dict[str, Any]] = {}
workers: dict[str, dict[str, Any]] = {}
task_queue: asyncio.Queue[str] = asyncio.Queue()

lock = asyncio.Lock()


class TaskRequest(BaseModel):
    kind: str = Field(default="demo", pattern=r"^[a-zA-Z0-9_-]{1,40}$")
    payload: dict[str, Any] = Field(default_factory=dict)


class WorkerRequest(BaseModel):
    worker_id: str = Field(min_length=1, max_length=100)
    name: str = Field(default="worker", max_length=100)
    capabilities: list[str] = Field(default_factory=lambda: ["demo"])
    cpu_count: int = Field(default=1, ge=1)
    gpu_available: bool = False
    gpu_name: str | None = None


class ClaimRequest(BaseModel):
    worker_id: str


class ResultRequest(BaseModel):
    worker_id: str
    result: dict[str, Any] = Field(default_factory=dict)


@app.get("/health")
async def health():
    return {
        "status": "online",
        "service": "NEXUS Distributed GPU",
        "queued_tasks": task_queue.qsize(),
        "registered_workers": len(workers),
    }


@app.post("/workers/register")
async def register_worker(request: WorkerRequest):
    async with lock:
        workers[request.worker_id] = {
            **request.model_dump(),
            "status": "idle",
            "last_seen": time.time(),
            "current_task": None,
        }

    return {
        "status": "registered",
        "worker_id": request.worker_id,
    }


@app.get("/workers")
async def list_workers():
    now = time.time()

    return [
        {
            **worker,
            "online": now - worker["last_seen"] < 30,
        }
        for worker in workers.values()
    ]


@app.post("/tasks", status_code=202)
async def create_task(request: TaskRequest):
    task_id = str(uuid.uuid4())

    task = {
        "task_id": task_id,
        "kind": request.kind,
        "payload": request.payload,
        "status": "queued",
        "created_at": time.time(),
        "updated_at": time.time(),
        "assigned_worker": None,
        "result": None,
        "error": None,
    }

    async with lock:
        tasks[task_id] = task
        await task_queue.put(task_id)

    return {
        "task_id": task_id,
        "status": "queued",
    }


@app.get("/tasks")
async def list_tasks():
    async with lock:
        return list(tasks.values())


@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    async with lock:
        task = tasks.get(task_id)

        if task is None:
            raise HTTPException(
                status_code=404,
                detail="Tarefa não encontrada",
            )

        return dict(task)


@app.post("/tasks/claim")
async def claim_task(request: ClaimRequest):
    async with lock:
        worker = workers.get(request.worker_id)

        if worker is None:
            raise HTTPException(
                status_code=404,
                detail="Worker não registrado",
            )

        worker["last_seen"] = time.time()

        if worker["status"] == "busy":
            return {"task": None, "reason": "worker_busy"}

        # Procura uma tarefa compatível sem bloquear a API.
        for _ in range(task_queue.qsize()):
            task_id = await task_queue.get()
            task = tasks.get(task_id)

            if task is None or task["status"] != "queued":
                continue

            capabilities = worker["capabilities"]

            if task["kind"] not in capabilities and "*" not in capabilities:
                await task_queue.put(task_id)
                continue

            task["status"] = "running"
            task["assigned_worker"] = request.worker_id
            task["updated_at"] = time.time()

            worker["status"] = "busy"
            worker["current_task"] = task_id

            return {
                "task": {
                    "task_id": task_id,
                    "kind": task["kind"],
                    "payload": task["payload"],
                }
            }

    return {"task": None, "reason": "no_compatible_task"}


@app.post("/tasks/{task_id}/complete")
async def complete_task(task_id: str, request: ResultRequest):
    async with lock:
        task = tasks.get(task_id)
        worker = workers.get(request.worker_id)

        if task is None or worker is None:
            raise HTTPException(
                status_code=404,
                detail="Tarefa ou worker não encontrado",
            )

        if (
            task["status"] != "running"
            or task["assigned_worker"] != request.worker_id
        ):
            raise HTTPException(
                status_code=409,
                detail="A tarefa não pertence a este worker",
            )

        task["status"] = "completed"
        task["result"] = request.result
        task["updated_at"] = time.time()

        worker["status"] = "idle"
        worker["current_task"] = None
        worker["last_seen"] = time.time()

    return {
        "status": "completed",
        "task_id": task_id,
    }


@app.post("/tasks/{task_id}/fail")
async def fail_task(task_id: str, request: ResultRequest):
    async with lock:
        task = tasks.get(task_id)
        worker = workers.get(request.worker_id)

        if task is None or worker is None:
            raise HTTPException(
                status_code=404,
                detail="Tarefa ou worker não encontrado",
            )

        if (
            task["status"] != "running"
            or task["assigned_worker"] != request.worker_id
        ):
            raise HTTPException(
                status_code=409,
                detail="A tarefa não pertence a este worker",
            )

        task["status"] = "failed"
        task["error"] = str(request.result.get("error", "Erro desconhecido"))
        task["updated_at"] = time.time()

        worker["status"] = "idle"
        worker["current_task"] = None
        worker["last_seen"] = time.time()

    return {
        "status": "failed",
        "task_id": task_id,
    }
