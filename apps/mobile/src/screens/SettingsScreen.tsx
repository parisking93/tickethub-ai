import { useEffect, useState } from 'react';
import { StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../App';
import { api } from '../api/client';
import { getBackendUrl, setBackendUrl } from '../config/backend';
import { colors } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'Settings'>;

export function SettingsScreen({ navigation }: Props): JSX.Element {
  const [url, setUrl] = useState('');
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    setUrl(getBackendUrl());
  }, []);

  const save = async (): Promise<void> => {
    await setBackendUrl(url.trim());
    setStatus('Salvato.');
  };

  const testConnection = async (): Promise<void> => {
    await setBackendUrl(url.trim());
    setStatus('Verifico…');
    try {
      const tickets = await api.tickets.list();
      setStatus(`Connesso ✓ (${tickets.length} ticket)`);
    } catch (err) {
      setStatus(`Errore: ${err instanceof Error ? err.message : 'connessione fallita'}`);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.label}>URL del backend desktop</Text>
      <Text style={styles.hint}>
        Es. http://192.168.1.50:8000 — il PC deve essere acceso e il backend in ascolto su 0.0.0.0,
        sulla stessa rete del telefono.
      </Text>
      <TextInput
        style={styles.input}
        value={url}
        onChangeText={setUrl}
        autoCapitalize="none"
        autoCorrect={false}
        keyboardType="url"
        placeholder="http://192.168.1.50:8000"
        placeholderTextColor={colors.textMuted}
      />

      <View style={styles.row}>
        <TouchableOpacity style={styles.btn} onPress={() => void save()}>
          <Text style={styles.btnText}>Salva</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.btn, styles.btnPrimary]} onPress={() => void testConnection()}>
          <Text style={styles.btnText}>Verifica connessione</Text>
        </TouchableOpacity>
      </View>

      {status && <Text style={styles.status}>{status}</Text>}

      <TouchableOpacity style={styles.linkBtn} onPress={() => navigation.goBack()}>
        <Text style={styles.link}>← Torna ai ticket</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg, padding: 16 },
  label: { color: colors.text, fontSize: 15, fontWeight: '600', marginBottom: 4 },
  hint: { color: colors.textMuted, fontSize: 12, marginBottom: 12 },
  input: {
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 6,
    color: colors.text,
    padding: 12,
  },
  row: { flexDirection: 'row', gap: 10, marginTop: 12 },
  btn: {
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 6,
    paddingVertical: 10,
    paddingHorizontal: 16,
  },
  btnPrimary: { backgroundColor: colors.primary, borderColor: colors.primary },
  btnText: { color: colors.text, fontWeight: '600' },
  status: { color: colors.textMuted, marginTop: 14 },
  linkBtn: { marginTop: 24 },
  link: { color: colors.primary },
});
