import { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import {
  STATUS_LABELS,
  TYPE_LABELS,
  TicketStatus,
  type Ticket,
} from '@tickethub/shared';
import type { RootStackParamList } from '../App';
import { api } from '../api/client';
import { colors, statusColor } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'TicketDetail'>;

// Transizioni esposte come azioni rapide da mobile.
const ACTIONS: Partial<Record<TicketStatus, TicketStatus[]>> = {
  [TicketStatus.Creato]: [TicketStatus.InLavorazione],
  [TicketStatus.InAttesa]: [TicketStatus.Approvato, TicketStatus.Rifiutato],
  [TicketStatus.Approvato]: [TicketStatus.Concluso],
};

export function TicketDetailScreen({ route }: Props): JSX.Element {
  const { ticketId } = route.params;
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [reviewNote, setReviewNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setTicket(await api.tickets.get(ticketId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore caricamento');
    }
  }, [ticketId]);

  useFocusEffect(
    useCallback(() => {
      void load();
    }, [load]),
  );

  const changeStatus = async (status: TicketStatus): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const note = status === TicketStatus.Rifiutato ? reviewNote || undefined : undefined;
      await api.tickets.updateStatus(ticketId, { status, review_note: note });
      setReviewNote('');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore aggiornamento');
    } finally {
      setBusy(false);
    }
  };

  if (!ticket) {
    return (
      <View style={styles.center}>
        {error ? <Text style={styles.error}>⚠ {error}</Text> : <ActivityIndicator color={colors.primary} />}
      </View>
    );
  }

  const actions = ACTIONS[ticket.status] ?? [];

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 32 }}>
      <View style={styles.row}>
        <Text style={styles.muted}>#{ticket.id} · {TYPE_LABELS[ticket.type]}</Text>
        <Text style={[styles.badge, { color: statusColor[ticket.status] }]}>
          {STATUS_LABELS[ticket.status]}
        </Text>
      </View>
      <Text style={styles.title}>{ticket.title}</Text>
      {ticket.description ? <Text style={styles.body}>{ticket.description}</Text> : null}

      {ticket.ai_note ? (
        <View style={styles.note}>
          <Text style={styles.noteLabel}>AI</Text>
          <Text style={styles.body}>{ticket.ai_note}</Text>
        </View>
      ) : null}

      {ticket.ai_draft ? (
        <View style={styles.draft}>
          <Text style={styles.noteLabel}>Bozza / piano</Text>
          <Text style={styles.mono}>{ticket.ai_draft}</Text>
        </View>
      ) : null}

      {ticket.branch_name ? <Text style={styles.mono}>branch: {ticket.branch_name}</Text> : null}

      {ticket.status === TicketStatus.InAttesa && (
        <TextInput
          style={styles.input}
          placeholder="Nota (per rifiuto)…"
          placeholderTextColor={colors.textMuted}
          value={reviewNote}
          onChangeText={setReviewNote}
        />
      )}

      {error && <Text style={styles.error}>⚠ {error}</Text>}

      <View style={styles.actions}>
        {actions.map((status) => (
          <TouchableOpacity
            key={status}
            style={[styles.actionBtn, { borderColor: statusColor[status] }]}
            disabled={busy}
            onPress={() => void changeStatus(status)}
          >
            <Text style={[styles.actionText, { color: statusColor[status] }]}>
              {STATUS_LABELS[status]}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg, padding: 16 },
  center: { flex: 1, backgroundColor: colors.bg, justifyContent: 'center', alignItems: 'center' },
  row: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 },
  muted: { color: colors.textMuted, fontSize: 13 },
  badge: { fontSize: 13, fontWeight: '600' },
  title: { color: colors.text, fontSize: 18, fontWeight: '600', marginBottom: 8 },
  body: { color: colors.text, fontSize: 14, lineHeight: 20 },
  note: { backgroundColor: colors.surface, borderRadius: 8, padding: 10, marginTop: 10 },
  draft: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 8,
    padding: 10,
    marginTop: 10,
  },
  noteLabel: { color: colors.textMuted, fontSize: 11, textTransform: 'uppercase', marginBottom: 4 },
  mono: { color: colors.text, fontFamily: 'monospace', fontSize: 12, marginTop: 6 },
  input: {
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 6,
    color: colors.text,
    padding: 10,
    marginTop: 12,
  },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginTop: 16 },
  actionBtn: { borderWidth: 1, borderRadius: 6, paddingVertical: 8, paddingHorizontal: 14 },
  actionText: { fontSize: 14, fontWeight: '600' },
  error: { color: '#ef4444', marginTop: 10 },
});
