import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Navigate, NavLink, Route, Routes, useNavigate } from "react-router-dom";
import { EQUIPMENT_PRESETS, GOAL_PRESETS, api, storage } from "./api";
import { MuscleMap, StatusBar, Stick } from "./figures";
import type { CoachResult, ExercisePublic, UserPublic, WorkoutPlanDay, WorkoutPublic } from "./types";

function todayIndex(user: UserPublic) {
  if (!user.current_plan?.days.length) return 0;
  return user.sessions_completed % user.current_plan.days.length;
}

function Phone({ children, nav = true }: { children: ReactNode; nav?: boolean }) {
  return (
    <div className="stage">
      <div className="phone">
        <StatusBar />
        <div className="screen">{children}</div>
        {nav && (
          <nav className="nav">
            <NavLink to="/" end className={({ isActive }) => (isActive ? "on" : "")}>
              ⌂<span>Home</span>
            </NavLink>
            <NavLink to="/plan" className={({ isActive }) => (isActive ? "on" : "")}>
              ▤<span>Plan</span>
            </NavLink>
            <NavLink to="/progress" className={({ isActive }) => (isActive ? "on" : "")}>
              ◉<span>Progress</span>
            </NavLink>
            <NavLink to="/coach" className={({ isActive }) => (isActive ? "on" : "")}>
              ●<span>Coach</span>
            </NavLink>
          </nav>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [catalog, setCatalog] = useState<ExercisePublic[]>([]);
  const [ready, setReady] = useState(false);

  async function refresh(id = storage.userId()) {
    if (!id) {
      setUser(null);
      setReady(true);
      return;
    }
    try {
      const [next, exercises] = await Promise.all([api.getUser(id), api.exercises()]);
      setUser(next);
      setCatalog(exercises);
    } catch {
      storage.clearUser();
      setUser(null);
    } finally {
      setReady(true);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  if (!ready) {
    return (
      <Phone nav={false}>
        <p className="lede">Loading…</p>
      </Phone>
    );
  }

  return (
    <Routes>
      <Route
        path="/onboarding"
        element={user ? <Navigate to="/" replace /> : <Onboarding onCreated={refresh} />}
      />
      <Route
        path="/*"
        element={
          !user ? (
            <Navigate to="/onboarding" replace />
          ) : (
            <Authed user={user} catalog={catalog} onRefresh={() => refresh(user.id)} />
          )
        }
      />
    </Routes>
  );
}

function Authed({
  user,
  catalog,
  onRefresh,
}: {
  user: UserPublic;
  catalog: ExercisePublic[];
  onRefresh: () => void;
}) {
  const byId = useMemo(() => Object.fromEntries(catalog.map((item) => [item.id, item])), [catalog]);
  return (
    <Routes>
      <Route path="/" element={<Home user={user} byId={byId} />} />
      <Route path="/plan" element={<Plan user={user} byId={byId} />} />
      <Route path="/session" element={<Session user={user} byId={byId} onDone={onRefresh} />} />
      <Route path="/summary" element={<Summary user={user} />} />
      <Route path="/progress" element={<Progress user={user} />} />
      <Route path="/coach" element={<Coach user={user} />} />
    </Routes>
  );
}

function Onboarding({ onCreated }: { onCreated: (id?: string) => Promise<void> }) {
  const [name, setName] = useState("Riya");
  const [goal, setGoal] = useState("muscle");
  const [days, setDays] = useState(4);
  const [gear, setGear] = useState("gym");
  const [age, setAge] = useState<"beginner" | "intermediate" | "advanced">("beginner");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true);
    setError("");
    try {
      const user = await api.createUser({
        name,
        days_per_week: days,
        max_duration_minutes: 60,
        available_equipment: EQUIPMENT_PRESETS[gear],
        goal: GOAL_PRESETS[goal],
        training_age: age,
        injuries: [],
      });
      await api.createPlan(user.id);
      storage.setUserId(user.id);
      await onCreated(user.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create plan");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Phone nav={false}>
      <div className="hero-row">
        <div>
          <h1>Welcome!</h1>
          <p className="lede">Let’s set up your plan. It only takes a minute.</p>
        </div>
        <Stick pose="wave" />
      </div>
      <label className="label">What’s your name?</label>
      <input className="field" value={name} onChange={(e) => setName(e.target.value)} />
      <div className="card">
        <h2>What’s your main goal?</h2>
        <div className="choice-grid">
          {[
            ["muscle", "Build Muscle"],
            ["strength", "Strength"],
            ["fat", "Lose Fat"],
            ["fit", "Stay Fit"],
          ].map(([id, label]) => (
            <button key={id} className={`choice ${goal === id ? "on" : ""}`} onClick={() => setGoal(id)}>
              <span>{label}</span>
            </button>
          ))}
        </div>
      </div>
      <div className="card">
        <h2>How many days per week?</h2>
        <div className="row">
          {[3, 4, 5, 6].map((n) => (
            <button key={n} className={`chip ${days === n ? "on" : ""}`} onClick={() => setDays(n)}>
              {n}
            </button>
          ))}
        </div>
      </div>
      <div className="card">
        <h2>What equipment do you have?</h2>
        <div className="choice-grid">
          {[
            ["gym", "Gym"],
            ["dumbbells", "Dumbbells"],
            ["home", "Home Gym"],
            ["bodyweight", "Bodyweight"],
          ].map(([id, label]) => (
            <button key={id} className={`choice ${gear === id ? "on" : ""}`} onClick={() => setGear(id)}>
              <span>{label}</span>
            </button>
          ))}
        </div>
      </div>
      <div className="card">
        <h2>What’s your experience level?</h2>
        <div className="row">
          {(["beginner", "intermediate", "advanced"] as const).map((item) => (
            <button key={item} className={`pill ${age === item ? "on" : ""}`} onClick={() => setAge(item)}>
              {item[0].toUpperCase() + item.slice(1)}
            </button>
          ))}
        </div>
      </div>
      {error && <p className="err">{error}</p>}
      <button className="primary" disabled={busy} onClick={() => void submit()}>
        {busy ? "Creating…" : "Create My Plan →"}
      </button>
    </Phone>
  );
}

function Home({ user, byId }: { user: UserPublic; byId: Record<string, ExercisePublic> }) {
  const navigate = useNavigate();
  const day = user.current_plan?.days[todayIndex(user)];
  const muscles = dayMuscles(day, byId);
  if (!day) {
    return (
      <Phone>
        <p>No plan yet.</p>
      </Phone>
    );
  }
  return (
    <Phone>
      <div className="hero-row">
        <div>
          <h1>Today’s Workout</h1>
          <p className="lede">{day.label}</p>
        </div>
        <Stick pose="flex" />
      </div>
      <div className="card">
        <h2>Workout Overview</h2>
        <div className="stats">
          <div className="stat">
            <b>{day.exercises.length}</b>
            <span>Exercises</span>
          </div>
          <div className="stat">
            <b>{day.estimated_minutes}</b>
            <span>Minutes</span>
          </div>
        </div>
        <p className="lede" style={{ marginTop: 12 }}>
          Focus {prettyList(muscles.slice(0, 3)) || pretty(day.focus)}
        </p>
      </div>
      {day.exercises.map((item) => (
        <div className="exercise" key={item.exercise_id}>
          <div className="icon">↳</div>
          <div>
            <b>{byId[item.exercise_id]?.name || item.exercise_id}</b>
            <small>
              {item.sets} sets × {item.rep_min}–{item.rep_max} reps
            </small>
          </div>
        </div>
      ))}
      <button className="primary" onClick={() => navigate("/session")}>
        Start Workout →
      </button>
    </Phone>
  );
}

function Plan({ user, byId }: { user: UserPublic; byId: Record<string, ExercisePublic> }) {
  const days = user.current_plan?.days || [];
  const [index, setIndex] = useState(todayIndex(user));
  const day = days[index];
  const muscles = dayMuscles(day, byId);
  return (
    <Phone>
      <h1>Muscle Focus</h1>
      <p className="lede">Primary muscles targeted</p>
      <div className="row" style={{ marginBottom: 12 }}>
        {days.map((item) => (
          <button
            key={item.day_index}
            className={`chip ${index === item.day_index ? "on" : ""}`}
            onClick={() => setIndex(item.day_index)}
          >
            {item.day_index + 1}
          </button>
        ))}
      </div>
      <MuscleMap active={muscles} />
      <div className="legend">
        <span>
          <i className="dot" style={{ background: "#111" }} /> Primary
        </span>
        <span>
          <i className="dot" style={{ background: "#d8d8d8" }} /> Rest
        </span>
      </div>
      {day && (
        <div className="card">
          <h2>{day.label}</h2>
          <p className="lede">{pretty(day.focus)}. Today we’re focusing on these patterns to build strength.</p>
          {day.exercises.map((item) => (
            <div key={item.exercise_id}>
              {byId[item.exercise_id]?.name || item.exercise_id}
            </div>
          ))}
        </div>
      )}
    </Phone>
  );
}

function Session({
  user,
  byId,
  onDone,
}: {
  user: UserPublic;
  byId: Record<string, ExercisePublic>;
  onDone: () => void;
}) {
  const navigate = useNavigate();
  const day = user.current_plan?.days[todayIndex(user)];
  const [workout, setWorkout] = useState<WorkoutPublic | null>(null);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState<Record<string, { weight: string; reps: string }>>({});

  useEffect(() => {
    if (!day) return;
    void (async () => {
      try {
        const started = await api.startWorkout(user.id, day.day_index);
        storage.setWorkoutId(started.id);
        setWorkout(started);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not start workout");
      }
    })();
  }, [day, user.id]);

  async function logSet(exerciseId: string, setIndex: number) {
    if (!workout) return;
    const key = `${exerciseId}-${setIndex}`;
    const row = logs[key] || { weight: "", reps: "" };
    await api.logSet(workout.id, {
      exercise_id: exerciseId,
      set_index: setIndex,
      weight_kg: row.weight ? Number(row.weight) : null,
      reps: Number(row.reps || 0),
      rir: 2,
    });
  }

  async function finish() {
    if (!workout) return;
    const done = await api.completeWorkout(workout.id);
    sessionStorage.setItem("ptp_last_workout", JSON.stringify(done));
    storage.clearWorkout();
    onDone();
    navigate("/summary");
  }

  if (!day) return <Phone><p>No day to train.</p></Phone>;

  return (
    <Phone>
      <h1>{day.label}</h1>
      <p className="lede">Log each set, then finish.</p>
      {day.exercises.map((item) => (
        <div className="card" key={item.exercise_id}>
          <h2>{byId[item.exercise_id]?.name || item.exercise_id}</h2>
          <div className="sets">
            {Array.from({ length: item.sets }, (_, setIndex) => {
              const key = `${item.exercise_id}-${setIndex}`;
              const row = logs[key] || { weight: "", reps: String(item.rep_min) };
              return (
                <div className="set-row" key={key}>
                  <b>{setIndex + 1}</b>
                  <input
                    inputMode="decimal"
                    placeholder="kg"
                    value={row.weight}
                    onChange={(e) => setLogs({ ...logs, [key]: { ...row, weight: e.target.value } })}
                  />
                  <input
                    inputMode="numeric"
                    placeholder="reps"
                    value={row.reps}
                    onChange={(e) => setLogs({ ...logs, [key]: { ...row, reps: e.target.value } })}
                  />
                  <button className="tiny" onClick={() => void logSet(item.exercise_id, setIndex)}>
                    Log
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      ))}
      {error && <p className="err">{error}</p>}
      <button className="primary" onClick={() => void finish()}>
        Finish Workout →
      </button>
    </Phone>
  );
}

function Summary({ user }: { user: UserPublic }) {
  const navigate = useNavigate();
  const [mood, setMood] = useState("good");
  const workout = useMemo(() => {
    const raw = sessionStorage.getItem("ptp_last_workout");
    return raw ? (JSON.parse(raw) as WorkoutPublic) : null;
  }, []);
  const sets = workout?.sets.length || 0;
  const volume = Math.round(
    (workout?.sets || []).reduce((sum, row) => sum + (row.weight_kg || 0) * row.reps, 0),
  );
  const minutes = workout
    ? Math.max(
        1,
        Math.round(
          (new Date(workout.completed_at || Date.now()).getTime() - new Date(workout.started_at).getTime()) /
            60000,
        ),
      )
    : 0;

  return (
    <Phone>
      <div className="hero-row">
        <div>
          <h1>Great Work!</h1>
          <p className="lede">You crushed it today, {user.name}.</p>
        </div>
        <Stick pose="celebrate" />
      </div>
      <div className="card">
        <h2>Workout Summary</h2>
        <div className="stats">
          <div className="stat">
            <b>{sets}</b>
            <span>Total Sets</span>
          </div>
          <div className="stat">
            <b>{minutes}</b>
            <span>Minutes</span>
          </div>
          <div className="stat">
            <b>{volume}</b>
            <span>kg volume</span>
          </div>
          <div className="stat">
            <b>{user.sessions_completed}</b>
            <span>Sessions</span>
          </div>
        </div>
      </div>
      <div className="card">
        <h2>How did you feel?</h2>
        <div className="mood">
          {[
            ["hard", "😣"],
            ["ok", "😐"],
            ["good", "🙂"],
          ].map(([id, face]) => (
            <button key={id} className={mood === id ? "on" : ""} onClick={() => setMood(id)}>
              {face}
            </button>
          ))}
        </div>
      </div>
      <button className="primary" onClick={() => navigate("/coach")}>
        Ask Coach →
      </button>
      <button className="ghost" style={{ marginTop: 10 }} onClick={() => navigate("/progress")}>
        View Progress
      </button>
    </Phone>
  );
}

function Progress({ user }: { user: UserPublic }) {
  const [rows, setRows] = useState<WorkoutPublic[]>([]);
  useEffect(() => {
    void api.history(user.id).then(setRows);
  }, [user.id]);
  return (
    <Phone>
      <h1>Progress</h1>
      <p className="lede">{user.sessions_completed} sessions completed</p>
      {rows.map((item) => (
        <div className="card" key={item.id}>
          <h2>{item.label}</h2>
          <p className="lede">
            {item.sets.length} sets · {item.completed_at ? "Done" : "In progress"}
          </p>
        </div>
      ))}
      {!rows.length && <p className="lede">Finish a workout to see history here.</p>}
    </Phone>
  );
}

function Coach({ user }: { user: UserPublic }) {
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<CoachResult | null>(null);

  async function ask(text: string) {
    setBusy(true);
    try {
      setResult(await api.coach(user.id, text));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Phone>
      <div className="hero-row">
        <div>
          <h1>Coach</h1>
          <p className="lede">Your AI training partner</p>
        </div>
        <Stick pose="coach" />
      </div>
      <div className="chat">Hey there! I’m here to help you train smarter. What would you like help with today?</div>
      {[
        "Why hasn't my bench improved?",
        "Give me a substitute for cable fly",
        "How is my recovery looking?",
      ].map((prompt) => (
        <button key={prompt} className="ghost" style={{ marginBottom: 8 }} onClick={() => void ask(prompt)}>
          {prompt}
        </button>
      ))}
      {result && (
        <div className="chat">
          {result.answer}
          {result.grounded && <div className="evidence">Grounded in your training log</div>}
        </div>
      )}
      <div className="composer">
        <input
          value={message}
          placeholder="Ask me anything..."
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && message.trim()) void ask(message);
          }}
        />
        <button disabled={busy || !message.trim()} onClick={() => void ask(message)}>
          ➤
        </button>
      </div>
    </Phone>
  );
}

function dayMuscles(day: WorkoutPlanDay | undefined, byId: Record<string, ExercisePublic>) {
  if (!day) return [];
  return [
    ...new Set(day.exercises.flatMap((item) => byId[item.exercise_id]?.primary_muscles || [])),
  ];
}

function pretty(value: string) {
  return value.replaceAll("_", " ");
}

function prettyList(values: string[]) {
  return values.map(pretty).join(", ");
}
