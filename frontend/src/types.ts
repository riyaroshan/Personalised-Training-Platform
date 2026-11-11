export type Goal = "hypertrophy" | "strength" | "general";
export type TrainingAge = "beginner" | "intermediate" | "advanced";

export type ExercisePublic = {
  id: string;
  name: string;
  movement_pattern: string;
  primary_muscles: string[];
  secondary_muscles: string[];
  equipment: string[];
  difficulty: number;
  is_compound: boolean;
  substitution_group: string;
};

export type ExercisePrescription = {
  exercise_id: string;
  sets: number;
  rep_min: number;
  rep_max: number;
  target_rir: number;
  target_weight_kg: number | null;
  rest_seconds: number;
};

export type WorkoutPlanDay = {
  day_index: number;
  label: string;
  focus: string;
  estimated_minutes: number;
  exercises: ExercisePrescription[];
};

export type WorkoutPlan = {
  days_per_week: number;
  split: string;
  days: WorkoutPlanDay[];
  reasoning: string;
};

export type UserPublic = {
  id: string;
  name: string;
  days_per_week: number;
  max_duration_minutes: number;
  available_equipment: string[];
  injuries: string[];
  goal: string;
  training_age: string;
  sessions_completed: number;
  current_plan: WorkoutPlan | null;
};

export type LoggedSet = {
  id: string;
  exercise_id: string;
  set_index: number;
  weight_kg: number | null;
  reps: number;
  rpe: number | null;
  rir: number | null;
  completed_at: string;
};

export type WorkoutPublic = {
  id: string;
  user_id: string;
  day_index: number;
  label: string;
  started_at: string;
  completed_at: string | null;
  sets: LoggedSet[];
};

export type CoachResult = {
  answer: string;
  evidence: string[];
  grounded: boolean;
  tool_calls: { name: string; arguments: Record<string, unknown>; ok: boolean }[];
  generation: { source: string; prompt_version: string | null; fallback_reason: string | null };
  plan_updated: boolean;
};
