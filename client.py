#!/usr/bin/env python3
import json
import shlex
import requests

BASE = "http://localhost:8000"

HELP = """
commands (strings must be quoted, ids are bare numbers):

  todos list
  todos add "title"
  todos done <id>
  todos delete <id>

  goals list
  goals add "title"
  goals done <id>
  goals delete <id>

  diary list
  diary add "body"
  diary delete <id>

  sleep list
  sleep add "2026-10-19T23:30:00"
  sleep wakeup <id> "2026-10-20T07:00:00"
  sleep delete <id>

  reminders list
  reminders add "title" "2026-10-20T09:00:00"
  reminders sent <id>
  reminders delete <id>

  help
  q
"""


def expect(value, kind):
    """Return the parsed value, or None when the quoting doesn't match the kind."""
    quoted = len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'"
    if kind == "int":
        if quoted or not value.isdigit():
            return None
        return int(value)
    if not quoted:
        return None
    return value[1:-1]


def warn(command, value, kind):
    wanted = "a number" if kind == "int" else "a quoted string"
    got = "a string" if value[:1] in "\"'" else "a number" if value.isdigit() else "unquoted text"
    print(f"{command} takes {wanted}, got {got}: {value}")


def call(method, path, body=None):
    r = requests.request(method, BASE + path, json=body)
    print(r.status_code)
    try:
        print(json.dumps(r.json(), indent=2, default=str))
    except ValueError:
        print(r.text)


def main():
    print("life-api client. type 'help' for commands, 'q' to quit.")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line == "q":
            break
        if line == "help":
            print(HELP)
            continue

        try:
            parts = shlex.split(line, posix=False)
        except ValueError as e:
            print(f"could not parse line: {e}")
            continue

        resource, action = parts[0], parts[1] if len(parts) > 1 else ""
        args = parts[2:]
        command = f"{resource} {action}".strip()

        # --- list: no arguments, just GET ---
        if action == "list" and resource in ("todos", "goals", "diary", "sleep", "reminders"):
            if args:
                print(f"{command} takes no arguments")
                continue
            call("GET", f"/{resource}")
            continue

        # --- single quoted string ---
        if command in ("todos add", "goals add", "diary add", "sleep add"):
            if len(args) != 1:
                print(f'{command} takes one quoted string, e.g. {command} "something"')
                continue
            value = expect(args[0], "str")
            if value is None:
                warn(command, args[0], "str")
                continue
            field = "body" if resource == "diary" else "slept_at" if resource == "sleep" else "title"
            call("POST", f"/{resource}", {field: value})
            continue

        # --- reminders add: two quoted strings ---
        if command == "reminders add":
            if len(args) != 2:
                print('reminders add takes two quoted strings: reminders add "title" "2026-10-20T09:00:00"')
                continue
            title = expect(args[0], "str")
            if title is None:
                warn("reminders add (title)", args[0], "str")
                continue
            when = expect(args[1], "str")
            if when is None:
                warn("reminders add (remind_at)", args[1], "str")
                continue
            call("POST", "/reminders", {"title": title, "remind_at": when})
            continue

        # --- single number ---
        single_id = {
            "todos done": ("PATCH", "/todos/{id}/done"),
            "todos delete": ("DELETE", "/todos/{id}"),
            "goals done": ("PATCH", "/goals/{id}/done"),
            "goals delete": ("DELETE", "/goals/{id}"),
            "diary delete": ("DELETE", "/diary/{id}"),
            "sleep delete": ("DELETE", "/sleep/{id}"),
            "reminders sent": ("PATCH", "/reminders/{id}/sent"),
            "reminders delete": ("DELETE", "/reminders/{id}"),
        }
        if command in single_id:
            if len(args) != 1:
                print(f"{command} takes one number, e.g. {command} 3")
                continue
            number = expect(args[0], "int")
            if number is None:
                warn(command, args[0], "int")
                continue
            method, path = single_id[command]
            call(method, path.replace("{id}", str(number)))
            continue

        # --- sleep wakeup: number then quoted string ---
        if command == "sleep wakeup":
            if len(args) != 2:
                print('sleep wakeup takes a number then a quoted string: sleep wakeup 5 "2026-10-20T07:00:00"')
                continue
            number = expect(args[0], "int")
            if number is None:
                warn("sleep wakeup (id)", args[0], "int")
                continue
            when = expect(args[1], "str")
            if when is None:
                warn("sleep wakeup (woke_at)", args[1], "str")
                continue
            call("PATCH", f"/sleep/{number}/wakeup", {"woke_at": when})
            continue

        print(f"unknown command: {command or line}. type 'help' to see commands.")


if __name__ == "__main__":
    main()
