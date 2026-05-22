import { useState } from 'react';
import type { CreateProjectInput } from '@tickethub/shared';

interface AddProjectFormProps {
  onAdd: (input: CreateProjectInput) => Promise<void>;
}

export function AddProjectForm({ onAdd }: AddProjectFormProps): JSX.Element {
  const [name, setName] = useState('');
  const [repoPath, setRepoPath] = useState('');
  const [defaultBranch, setDefaultBranch] = useState('main');
  const [testCommand, setTestCommand] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await onAdd({
        name: name.trim(),
        repo_path: repoPath.trim(),
        default_branch: defaultBranch.trim() || 'main',
        test_command: testCommand.trim() || null,
      });
      setName('');
      setRepoPath('');
      setTestCommand('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore creazione progetto');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="email-form" onSubmit={submit}>
      <div className="email-form__row">
        <input
          className="email-form__field"
          type="text"
          placeholder="nome progetto"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <input
          className="email-form__field"
          type="text"
          placeholder="branch principale"
          value={defaultBranch}
          onChange={(e) => setDefaultBranch(e.target.value)}
        />
      </div>
      <div className="email-form__row">
        <input
          className="email-form__field"
          type="text"
          placeholder="percorso assoluto del repository git"
          value={repoPath}
          onChange={(e) => setRepoPath(e.target.value)}
          required
        />
      </div>
      <div className="email-form__row">
        <input
          className="email-form__field"
          type="text"
          placeholder="comando di test (opzionale), es. pytest -q"
          value={testCommand}
          onChange={(e) => setTestCommand(e.target.value)}
        />
        <button className="btn btn--primary" type="submit" disabled={submitting}>
          {submitting ? 'Aggiungo…' : 'Aggiungi progetto'}
        </button>
      </div>
      {error && <p className="email-form__error">⚠ {error}</p>}
    </form>
  );
}
