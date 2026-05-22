import { useCallback, useLayoutEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { STATUS_LABELS, TYPE_LABELS, type Ticket } from '@tickethub/shared';
import type { RootStackParamList } from '../App';
import { api } from '../api/client';
import { colors, statusColor } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'Board'>;

export function BoardScreen({ navigation }: Props): JSX.Element {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [working, setWorking] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      setTickets(await api.tickets.list());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore di connessione al backend');
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      void load();
    }, [load]),
  );

  useLayoutEffect(() => {
    navigation.setOptions({
      headerRight: () => (
        <View style={styles.headerRow}>
          <TouchableOpacity onPress={() => void runJob()} disabled={working}>
            <Text style={styles.headerBtn}>{working ? '…' : '▶ Job'}</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={() => navigation.navigate('Settings')}>
            <Text style={styles.headerBtn}>⚙</Text>
          </TouchableOpacity>
        </View>
      ),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigation, working]);

  const runJob = async (): Promise<void> => {
    setWorking(true);
    try {
      await api.worker.run();
      await load();
    } catch {
      // l'errore viene mostrato al prossimo load
    } finally {
      setWorking(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {error && <Text style={styles.error}>⚠ {error}</Text>}
      <FlatList
        data={tickets}
        keyExtractor={(t) => String(t.id)}
        refreshControl={<RefreshControl refreshing={false} onRefresh={() => void load()} />}
        ListEmptyComponent={<Text style={styles.muted}>Nessun ticket.</Text>}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.card}
            onPress={() => navigation.navigate('TicketDetail', { ticketId: item.id })}
          >
            <View style={styles.cardHeader}>
              <Text style={styles.cardId}>#{item.id}</Text>
              <Text style={[styles.badge, { color: statusColor[item.status] }]}>
                {STATUS_LABELS[item.status]}
              </Text>
            </View>
            <Text style={styles.cardTitle}>{item.title}</Text>
            <Text style={styles.muted}>{TYPE_LABELS[item.type]}</Text>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg, padding: 12 },
  center: { flex: 1, backgroundColor: colors.bg, justifyContent: 'center' },
  headerRow: { flexDirection: 'row', gap: 16 },
  headerBtn: { color: colors.text, fontSize: 16 },
  error: { color: '#ef4444', marginBottom: 8 },
  muted: { color: colors.textMuted, fontSize: 13 },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    marginBottom: 10,
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 },
  cardId: { color: colors.textMuted, fontSize: 12 },
  badge: { fontSize: 12, fontWeight: '600' },
  cardTitle: { color: colors.text, fontSize: 15, marginBottom: 2 },
});
