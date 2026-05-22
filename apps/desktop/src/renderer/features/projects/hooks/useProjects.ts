import { useCallback, useEffect, useState } from 'react';
import type { CreateProjectInput, Project } from '@tickethub/shared';
import { projectsApi } from '../api/projectsApi';

interface UseProjectsResult {
  projects: Project[];
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
  addProject: (input: CreateProjectInput) => Promise<void>;
  removeProject: (id: number) => Promise<void>;
}

export function useProjects(): UseProjectsResult {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setProjects(await projectsApi.list());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore caricamento progetti');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const addProject = useCallback(
    async (input: CreateProjectInput) => {
      await projectsApi.create(input);
      await reload();
    },
    [reload],
  );

  const removeProject = useCallback(
    async (id: number) => {
      await projectsApi.remove(id);
      await reload();
    },
    [reload],
  );

  return { projects, loading, error, reload, addProject, removeProject };
}
