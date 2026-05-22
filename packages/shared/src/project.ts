/**
 * Contratti condivisi per i progetti git.
 * Allineati con backend/src/app/models/project.py e schemas/project.py.
 */

export interface Project {
  id: number;
  name: string;
  repo_path: string;
  default_branch: string;
  test_command: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateProjectInput {
  name: string;
  repo_path: string;
  default_branch?: string;
  test_command?: string | null;
}
