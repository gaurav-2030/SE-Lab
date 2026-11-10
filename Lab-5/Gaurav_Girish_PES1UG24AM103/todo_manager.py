"""To-do list and task manager for the Lab 5 static analysis exercise."""

import json
import secrets
import smtplib
from datetime import datetime
from email.message import EmailMessage

tasks = {}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def add_task(title, priority="medium", labels=None):
    """Add a task and return its generated task id.

    ``labels`` defaults to ``None`` instead of ``[]`` so that no list is
    shared between calls; a fresh list is built for each task.
    """
    task_id=len(tasks) + 1
    task_labels = list(labels) if labels else []
    task_labels.append(priority)
    tasks[task_id] = {"title": title, "priority": priority, "done": False,
                      "labels": task_labels,
                      "created": datetime.now().isoformat()}
    return task_id


def complete_task(task_id):
    """Mark a task as done. Return True when the task id exists."""
    if task_id in tasks:
        tasks[task_id]["done"] = True
        return True
    print("No task with id", task_id)
    return False


def pending_tasks():
    """Return the titles of unfinished tasks, highest priority first."""
    pending = [task for task in tasks.values() if not task["done"]]
    pending.sort(key=lambda task: PRIORITY_ORDER[task["priority"]])
    return [task["title"] for task in pending]


def find_task(keyword):
    """Return the id of the first task whose title contains *keyword*.

    Return ``None`` when no task matches, so that every exit path of the
    function returns a value.
    """
    for task_id, task in tasks.items():
        if keyword.lower() in task["title"].lower():
            return task_id
    return None



def save_tasks(file_name="tasks_store.json"):
    """Write every task to *file_name* as JSON.

    JSON is a data-only format, so reloading a store file can never
    execute code the way an unpickled file can.
    """
    with open(file_name, "w", encoding="utf-8") as handle:
        json.dump(tasks, handle, indent=2)


def load_tasks(file_name="tasks_store.json"):
    """Read and return the tasks stored in *file_name*.

    JSON object keys are always strings, so the task ids are converted
    back to integers to keep the in-memory shape unchanged.
    """
    with open(file_name, "r", encoding="utf-8") as handle:
        stored = json.load(handle)
    return {int(task_id): task for task_id, task in stored.items()}


def export_json(file_name="tasks.json"):
    """Export every task to *file_name* as indented JSON."""
    with open(file_name, "w", encoding="utf-8") as handle:
        json.dump(tasks, handle, indent=2)


def remind_by_email(address, host="localhost", port=25):
    """Mail the pending task list to *address* through an SMTP relay.

    No shell is involved, so the address can no longer be used to inject
    a command. It is validated first to rule out header injection.
    """
    if "@" not in address or "\r" in address or "\n" in address:
        raise ValueError("not a usable email address")
    message = EmailMessage()
    message["Subject"] = "Pending tasks"
    message["From"] = "todo-manager@localhost"
    message["To"] = address
    message.set_content("\n".join(pending_tasks()))
    with smtplib.SMTP(host, port) as relay:
        relay.send_message(message)


def main():
    """Run a short demonstration of the task manager."""
    add_task("Submit lab report", "high")
    add_task("Buy groceries")
    add_task("Call plumber", "low")
    add_task("Book train tickets", "high")
    complete_task(2)
    complete_task(99)
    print("Pending tasks:", pending_tasks())
    print("Task id for 'plumber':", find_task("plumber"))
    print("Task id for 'gym':", find_task("gym")) # returns None
    suggestion = secrets.choice(pending_tasks())
    print("Try this next:", suggestion)
    save_tasks()
    restored = load_tasks()
    print("Tasks restored from file:",len(restored))
    export_json()
    print("Exported tasks to tasks.json")


if __name__ == "__main__":
    main()
