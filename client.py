#!/usr/bin/env python3
import json
import shlex
import os
import requests

# override with API_BASE env var, e.g. export API_BASE=http://192.168.0.115:8000
BASE = os.environ.get("API_BASE", "http://192.168.0.101:8000")

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
  sleep add now
  sleep wakeup <id> now
  sleep delete <id>

  reminders list
  reminders add "title" "2026-10-20T09:00:00"
  reminders sent <id>
  reminders delete <id>

  sport list
  sport add "run" "2026-10-20"
  sport delete <id>

  eatings list
  eatings add "oatmeal with banana"
  eatings delete <id>

  steps list
  steps add "10000" "2026-10-20"
  steps delete <id>

  ideas list
  ideas add "my cool idea"
  ideas delete <id>


  help
  q
"""


def expect(value, kind):
    """Return the parsed value, or None when the quoting doesn't match the kind."""
    quoted = len(value) >= 2 and value[0] == value[-1] and value[0] in "\"\'"
    if kind == "int":
        if quoted or not value.isdigit():
            return None
        return int(value)
    if not quoted:
        return None
    return value[1:-1]


def warn(command, value, kind):
    wanted = "a number" if kind == "int" else "a quoted string"
    got = "a string" if value[:1] in "\"\'" else "a number" if value.isdigit() else "unquoted text"
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
        list_resources = ("todos", "goals", "diary", "sleep", "reminders",
                          "sport", "eatings", "steps", "ideas")
        if action == "list" and resource in list_resources:
            if args:
                print(f"{command} takes no arguments")
                continue
            call("GET", f"/{resource}")
            continue

        # --- single quoted string: todos, goals, diary, sleep, eatings, ideas ---
        single_str_cmds = ("todos add", "goals add", "diary add",
                           "eatings add", "ideas add")
        if command in single_str_cmds:
            if len(args) != 1:
                print(f'{command} takes one quoted string, e.g. {command} "something"')
                continue
            value = expect(args[0], "str")
            if value is None:
                warn(command, args[0], "str")
                continue
            if resource == "diary":
                field = "body"
            elif resource == "eatings":
                field = "description"
            else:
                field = "title"
            call("POST", f"/{resource}", {field: value})
            continue

        # --- sleep add: a quoted datetime, or the bare word now ---
        if command == "sleep add":
            if len(args) != 1:
                print('sleep add takes "now" or one quoted datetime: sleep add now')
                continue
            when = args[0]
            if when.lower() != "now":
                when = expect(when, "str")
                if when is None:
                    warn("sleep add", args[0], "str")
                    continue
            call("POST", "/sleep", {"slept_at": when})
            continue

        # --- reminders add: title then datetime ---
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

        # --- sport add: activity then date ---
        if command == "sport add":
            if len(args) != 2:
                print('sport add takes two quoted strings: sport add "run" "2026-10-20"')
                continue
            activity = expect(args[0], "str")
            if activity is None:
                warn("sport add (activity)", args[0], "str")
                continue
            day = expect(args[1], "str")
            if day is None:
                warn("sport add (done_on)", args[1], "str")
                continue
            call("POST", "/sport", {"activity": activity, "done_on": day})
            continue

        # --- steps add: count then date ---
        if command == "steps add":
            if len(args) != 2:
                print('steps add takes a number then a quoted date: steps add "10000" "2026-10-20"')
                continue
            count = expect(args[0], "str")   # comes in quoted, e.g. "10000"
            if count is None:
                warn("steps add (steps)", args[0], "str")
                continue
            day = expect(args[1], "str")
            if day is None:
                warn("steps add (recorded_on)", args[1], "str")
                continue
            try:
                count = int(count)
            except ValueError:
                print(f"steps add: steps must be a number, got: {count}")
                continue
            call("POST", "/steps", {"steps": count, "recorded_on": day})
            continue

        # --- single number: done / delete / sent ---
        single_id = {
            "todos done":         ("PATCH",  "/todos/{id}/done"),
            "todos delete":       ("DELETE", "/todos/{id}"),
            "goals done":         ("PATCH",  "/goals/{id}/done"),
            "goals delete":       ("DELETE", "/goals/{id}"),
            "diary delete":       ("DELETE", "/diary/{id}"),
            "sleep delete":       ("DELETE", "/sleep/{id}"),
            "reminders sent":     ("PATCH",  "/reminders/{id}/sent"),
            "reminders delete":   ("DELETE", "/reminders/{id}"),
            "sport delete":       ("DELETE", "/sport/{id}"),
            "eatings delete":     ("DELETE", "/eatings/{id}"),
            "steps delete":       ("DELETE", "/steps/{id}"),
            "ideas delete":       ("DELETE", "/ideas/{id}"),
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

        # --- sleep wakeup: id then a datetime, or the bare word now ---
        if command == "sleep wakeup":
            if len(args) != 2:
                print('sleep wakeup takes a number then "now" or a quoted datetime: sleep wakeup 5 now')
                continue
            number = expect(args[0], "int")
            if number is None:
                warn("sleep wakeup (id)", args[0], "int")
                continue
            when = args[1]
            if when.lower() != "now":
                when = expect(when, "str")
                if when is None:
                    warn("sleep wakeup (woke_at)", args[1], "str")
                    continue
            call("PATCH", f"/sleep/{number}/wakeup", {"woke_at": when})
            continue

        print(f"unknown command: {command or line}. type 'help' to see commands.")


if __name__ == "__main__":
    main()
