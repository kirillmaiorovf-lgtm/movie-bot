
user_sessions = {}
user_history = {}

def set_session(user_id: int, data: dict):
    user_sessions[user_id] = data

def get_session(user_id: int):
    return user_sessions.get(user_id, {})

def add_to_history(user_id: int, movie: dict):
    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append(movie)
    if len(user_history[user_id]) > 20:
        user_history[user_id].pop(0)
