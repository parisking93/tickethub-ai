import { useState } from 'react';
import { TYPE_LABELS, TicketType, type CreateTicketInput } from '@tickethub/shared';
import { useProjects } from '../../projects/hooks/useProjects';

interface CreateTicketFormProps {
  onCreate: (input: CreateTicketInput) => Promise<void>;
}

const isCodeType = (t: TicketType): boolean => t === TicketType.Fix || t === TicketType.Feature;

export function CreateTicketForm({ onCreate }: CreateTicketFormProps): JSX.Element {
  const { projects } = useProjects();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [type, setType] = useState<TicketType>(TicketType.Fix);
  const [projectId, setProjectId] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);

  const submit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!title.trim()) return;
    setSubmitting(true);
    try {
      await onCreate({
        title: title.trim(),
        description: description.trim() || null,
        type,
        project_id: isCodeType(type) && projectId ? Number(projectId) : null,
      });
      setTitle('');
      setDescription('');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="create-form" onSubmit={submit}>
      <input
        className="create-form__field"
        type="text"
        placeholder="Titolo del ticket"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        required
      />
      <input
        className="create-form__field"
        type="text"
        placeholder="Descrizione (opzionale)"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />
      <select
        className="create-form__field"
        value={type}
        onChange={(e) => setType(e.target.value as TicketType)}
      >
        {Object.values(TicketType).map((t) => (
          <option key={t} value={t}>
            {TYPE_LABELS[t]}
          </option>
        ))}
      </select>
      {isCodeType(type) && (
        <select
          className="create-form__field"
          value={projectId}
          onChange={(e) => setProjectId(e.target.value)}
        >
          <option value="">— progetto —</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      )}
      <button className="btn btn--primary" type="submit" disabled={submitting}>
        {submitting ? 'Creo…' : 'Nuovo ticket'}
      </button>
    </form>
  );
}
