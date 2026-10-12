import argparse
import os
import platform
import socket
import time
import uuid

import httpx


def detect_resources():
    cpu_count = os.cpu_count() or 1
    gpu_available = False
    gpu_name = None

    try:
        import psutil
        ram_gb = round(
            psutil.virtual_memory().total / (1024 ** 3), 2
        )
    except ImportError:
        ram_gb = None

    try:
        import torch

        if torch.cuda.is_available():
            gpu_available = True
            gpu_name = torch.cuda.get_device_name(0)

    except ImportError:
        pass

    return {
        "cpu_count": cpu_count,
        "ram_gb": ram_gb,
        "gpu_available": gpu_available,
        "gpu_name": gpu_name,
    }


def execute_task(kind, payload):
    # Nunca executar código arbitrário recebido pela rede.
    if kind == "demo":
        message = str(payload.get("text", ""))

        return {
            "message": "Tarefa processada pelo NEXUS Worker",
            "input": message,
            "characters": len(message),
            "worker_host": socket.gethostname(),
            "platform": platform.platform(),
            "processed_at": time.time(),
        }

    raise ValueError(f"Tipo de tarefa não suportado: {kind}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--coordinator",
        default="http://127.0.0.1:8787",
    )
    parser.add_argument(
        "--name",
        default="nexus-worker",
    )
    parser.add_argument(
        "--poll",
        type=float,
        default=2.0,
    )
    args = parser.parse_args()

    worker_id = str(uuid.uuid4())
    resources = detect_resources()

    registration = {
        "worker_id": worker_id,
        "name": args.name,
        "capabilities": ["demo"],
        "cpu_count": resources["cpu_count"],
        "gpu_available": resources["gpu_available"],
        "gpu_name": resources["gpu_name"],
    }

    print(f"Worker: {args.name}")
    print(f"CPU: {resources['cpu_count']} threads")
    print(f"RAM: {resources['ram_gb']} GB")
    print(f"GPU detectada: {resources['gpu_name'] or 'não detectada'}")

    with httpx.Client(
        base_url=args.coordinator.rstrip("/"),
        timeout=20,
    ) as client:

        response = client.post(
            "/workers/register",
            json=registration,
        )
        response.raise_for_status()

        print(f"Registrado: {worker_id}")
        print("Aguardando tarefas. Ctrl+C para encerrar.")

        while True:
            try:
                response = client.post(
                    "/tasks/claim",
                    json={"worker_id": worker_id},
                )
                response.raise_for_status()

                task = response.json().get("task")

                if task is None:
                    time.sleep(args.poll)
                    continue

                task_id = task["task_id"]
                print(f"Executando: {task_id}")

                try:
                    result = execute_task(
                        task["kind"],
                        task["payload"],
                    )

                    response = client.post(
                        f"/tasks/{task_id}/complete",
                        json={
                            "worker_id": worker_id,
                            "result": result,
                        },
                    )
                    response.raise_for_status()

                    print(f"Concluída: {task_id}")

                except Exception as exc:
                    client.post(
                        f"/tasks/{task_id}/fail",
                        json={
                            "worker_id": worker_id,
                            "result": {"error": str(exc)},
                        },
                    )
                    print(f"Falha: {exc}")

            except KeyboardInterrupt:
                break

            except Exception as exc:
                print(f"Erro de comunicação: {exc}")
                time.sleep(max(args.poll, 3))

    print("Worker encerrado.")


if __name__ == "__main__":
    main()
