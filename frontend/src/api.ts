import type {
  CoachResult,
  ExercisePublic,
  UserPublic,
  WorkoutPlan,
  WorkoutPublic,
} from "./types";

const USER_KEY = "ptp_user_id";
const WORKOUT_KEY = "ptp_workout_id";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export const storage = {
  userId: () => localStorage.getItem(USER_KEY),
  setUserId: (id: string) => localStorage.setItem(USER_KEY, id),
  clearUser: () => localStorage.removeItem(USER_KEY),
  workoutId: () => localStorage.getItem(WORKOUT_KEY),
  setWorkoutId: (id: string) => localStorage.setItem(WORKOUT_KEY, id),
  clearWorkout: () => localStorage.removeItem(WORKOUT_KEY),
};

export const api = {
  createUser: (body: Record<string, unknown>) =>
    request<UserPublic>("/v1/users", { method: "POST", body: JSON.stringify(body) }),
  getUser: (id: string) => request<UserPublic>(`/v1/users/${id}`),
  createPlan: (id: string) =>
    request<{ user_id: string; plan: WorkoutPlan }>(`/v1/users/${id}/plan`, { method: "POST" }),
  getPlan: (id: string) => request<{ plan: WorkoutPlan }>(`/v1/users/${id}/plan`),
  exercises: () => request<ExercisePublic[]>("/v1/exercises"),
  startWorkout: (userId: string, dayIndex: number) =>
    request<WorkoutPublic>(`/v1/users/${userId}/workouts`, {
      method: "POST",
      body: JSON.stringify({ day_index: dayIndex }),
    }),
  logSet: (workoutId: string, body: Record<string, unknown>) =>
    request(`/v1/workouts/${workoutId}/sets`, { method: "POST", body: JSON.stringify(body) }),
  completeWorkout: (workoutId: string) =>
    request<WorkoutPublic>(`/v1/workouts/${workoutId}/complete`, { method: "POST" }),
  history: (userId: string) => request<WorkoutPublic[]>(`/v1/users/${userId}/history`),
  substitutes: (exerciseId: string, userId: string) =>
    request<{ exercise: ExercisePublic; score: number }[]>(
      `/v1/exercises/${exerciseId}/substitutes?user_id=${userId}`,
    ),
  coach: (userId: string, message: string) =>
    request<CoachResult>(`/v1/users/${userId}/coach`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
};

export const EQUIPMENT_PRESETS: Record<string, string[]> = {
  gym: [
    "barbell",
    "dumbbell",
    "cable",
    "machine",
    "bodyweight",
    "kettlebell",
    "band",
    "smith",
    "ez_bar",
    "trap_bar",
  ],
  dumbbells: ["dumbbell", "bodyweight", "band", "kettlebell"],
  home: ["dumbbell", "kettlebell", "band", "bodyweight", "barbell", "ez_bar"],
  bodyweight: ["bodyweight", "band"],
};

export const GOAL_PRESETS: Record<string, "hypertrophy" | "strength" | "general"> = {
  muscle: "hypertrophy",
  strength: "strength",
  fat: "general",
  fit: "general",
};
