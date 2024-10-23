<script setup lang="ts">
import useMessages from '@/stores/messages'
import useNotifications from '@/stores/notifications'

function getPreferredTheme() {
  var preferredTheme = localStorage.getItem('colorTheme')
  if (!preferredTheme) {
    preferredTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return preferredTheme === 'dark' ? 'dark' : 'light'
}

const theme = ref<'light' | 'dark'>(getPreferredTheme())
const drawerOpen = ref(false)
const messages = useMessages()
const notifications = useNotifications()

function toggleTheme() {
  theme.value = theme.value === 'light' ? 'dark' : 'light'
}

function getMessageClass(message: any) {
  return {
    'text-error': message.type === 'error',
    'text-warning': message.type === 'warning',
    'text-success': message.type === 'success'
  }
}

watchEffect(() => {
  localStorage.setItem('colorTheme', theme.value)
  document.documentElement.style.colorScheme = theme.value
})

onMounted(() => {
  messages.addMessage({ text: 'Welcome to the RedPepper Console' })
})
</script>

<template>
  <v-app :theme="theme" id="v-app">
    <Teleport to="body">
      <v-alert
        v-for="(notification, i) in notifications.notifications"
        :key="notification.id"
        :type="notification.type"
        density="comfortable"
        :text="notification.text"
        style="z-index: 100000; position: fixed; right: 1em"
        :style="{ bottom: `${i * 4 + 1}em` }"
      >
      </v-alert>
    </Teleport>
    <v-app-bar height="48">
      <template #prepend>
        <v-app-bar-nav-icon @click="drawerOpen = !drawerOpen">
          <v-img alt="RedPepper logo" src="/assets/logo.svg" width="32" height="32" />
        </v-app-bar-nav-icon>
      </template>
      <v-app-bar-title text="RedPepper Console" class="text-primary" />
    </v-app-bar>
    <v-navigation-drawer v-model="drawerOpen">
      <v-list>
        <v-list-item to="/" role="option">Home</v-list-item>
        <v-list-item to="/login" role="option">Login</v-list-item>
        <v-list-item to="/agents" role="option">Agents</v-list-item>
        <v-list-item to="/events" role="option">Events</v-list-item>
        <v-list-item to="/commands" role="option">Commands</v-list-item>
        <v-list-item to="/data" role="option">Data Editor</v-list-item>
        <v-list-item to="/logout" role="option">Logout</v-list-item>
        <v-list-item to="/help" role="option">Help</v-list-item>
      </v-list>
    </v-navigation-drawer>
    <v-main class="bg-surface-light">
      <RouterView />
    </v-main>
    <v-footer app height="36">
      <span
        v-if="messages.currentMessage"
        v-text="messages.currentMessage.text"
        :class="getMessageClass(messages.currentMessage)"
      />
      <div class="me-auto" />
      <v-btn
        @click="toggleTheme"
        icon="mdi-theme-light-dark"
        density="comfortable"
        variant="flat"
      />
    </v-footer>
  </v-app>
</template>

<style lang="css">
body {
  font-size: 12pt;
  font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
