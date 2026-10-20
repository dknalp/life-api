-- tables the API expects. run once against the life database.
-- the older tables (goals, todos, sleep_logs, diary, reminders) were created
-- outside this repo; sport_days is the one added here.

CREATE TABLE IF NOT EXISTS sport_days (
    id SERIAL PRIMARY KEY,
    activity TEXT NOT NULL,
    done_on DATE NOT NULL,
    duration_minutes INTEGER,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- eatings: food log
CREATE TABLE IF NOT EXISTS eatings (
    id          SERIAL PRIMARY KEY,
    description TEXT NOT NULL,
    meal_type   TEXT,
    calories    INTEGER,
    eaten_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- step_logs: daily step count
CREATE TABLE IF NOT EXISTS step_logs (
    id          SERIAL PRIMARY KEY,
    steps       INTEGER NOT NULL,
    recorded_on DATE NOT NULL,
    notes       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ideas: quick capture of ideas
CREATE TABLE IF NOT EXISTS ideas (
    id         SERIAL PRIMARY KEY,
    title      TEXT NOT NULL,
    body       TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
