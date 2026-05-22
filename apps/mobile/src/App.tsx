import { useEffect, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import { loadBackendUrl } from './config/backend';
import { colors } from './theme';
import { BoardScreen } from './screens/BoardScreen';
import { TicketDetailScreen } from './screens/TicketDetailScreen';
import { SettingsScreen } from './screens/SettingsScreen';

export type RootStackParamList = {
  Board: undefined;
  TicketDetail: { ticketId: number };
  Settings: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

const navTheme = {
  ...DefaultTheme,
  dark: true,
  colors: {
    ...DefaultTheme.colors,
    background: colors.bg,
    card: colors.surface,
    text: colors.text,
    border: colors.border,
    primary: colors.primary,
  },
};

export function App(): JSX.Element {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    void loadBackendUrl().finally(() => setReady(true));
  }, []);

  if (!ready) {
    return (
      <View style={{ flex: 1, backgroundColor: colors.bg, justifyContent: 'center' }}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  return (
    <NavigationContainer theme={navTheme}>
      <StatusBar style="light" />
      <Stack.Navigator
        screenOptions={{
          headerStyle: { backgroundColor: colors.surface },
          headerTintColor: colors.text,
        }}
      >
        <Stack.Screen name="Board" component={BoardScreen} options={{ title: 'TicketHub AI' }} />
        <Stack.Screen
          name="TicketDetail"
          component={TicketDetailScreen}
          options={{ title: 'Ticket' }}
        />
        <Stack.Screen
          name="Settings"
          component={SettingsScreen}
          options={{ title: 'Impostazioni' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
