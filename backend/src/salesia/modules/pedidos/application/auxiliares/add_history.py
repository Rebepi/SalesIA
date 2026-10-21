import json

from salesia.modules.pedidos.application.auxiliares.now import now


def add_history(row, state, user, note):

    history = json.loads(row.history_json)

    history.append({"status": state, "timestamp": now().isoformat(), "actor": user.email, "note": note})

    row.history_json = json.dumps(history)
