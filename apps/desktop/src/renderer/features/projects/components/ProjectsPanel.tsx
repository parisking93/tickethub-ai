import type { Project } from '@tickethub/shared';
import { useProjects } from '../hooks/useProjects';
import { AddProjectForm } from './AddProjectForm';

interface ProjectsPanelProps {
  onClose: () => void;
}

export function ProjectsPanel({ onClose }: ProjectsPanelProps): JSX.Element {
  const { projects, loading, error, addProject, removeProject } = useProjects();

  return (
    <div className="drawer" role="dialog" aria-label="Progetti git">
      <div className="drawer__backdrop" onClick={onClose} />
      <aside className="drawer__panel">
        <header className="drawer__header">
          <h2>Progetti git</h2>
          <button className="btn btn--sm" type="button" onClick={onClose}>
            ✕
          </button>
        </header>

        <AddProjectForm onAdd={addProject} />

        {error && <p className="drawer__error">⚠ {error}</p>}
        {loading ? (
          <p className="drawer__muted">Caricamento…</p>
        ) : projects.length === 0 ? (
          <p className="drawer__muted">Nessun progetto registrato.</p>
        ) : (
          <ul className="account-list">
            {projects.map((p) => (
              <ProjectRow key={p.id} project={p} onRemove={() => void removeProject(p.id)} />
            ))}
          </ul>
        )}
      </aside>
    </div>
  );
}

function ProjectRow({
  project,
  onRemove,
}: {
  project: Project;
  onRemove: () => void;
}): JSX.Element {
  return (
    <li className="account-list__item">
      <div className="account-list__info">
        <span className="account-list__email">{project.name}</span>
        <span className="account-list__meta">
          {project.repo_path} · branch {project.default_branch}
          {project.test_command ? ` · test: ${project.test_command}` : ''}
        </span>
      </div>
      <div className="account-list__actions">
        <button className="btn btn--sm btn--rifiutato" type="button" onClick={onRemove}>
          Elimina
        </button>
      </div>
    </li>
  );
}
