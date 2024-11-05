<script setup lang="ts">
import { useDisplay } from 'vuetify'

function getPreferredTheme() {
  var preferredTheme = localStorage.getItem('colorTheme')
  if (!preferredTheme) {
    preferredTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return preferredTheme === 'dark' ? 'dark' : 'light'
}

const theme = ref<'light' | 'dark'>(getPreferredTheme())
const display = useDisplay()
const messages = useMessages()
const notifications = useNotifications()
const user = useUser()

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
  user.refresh()
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
        <v-img alt="RedPepper logo" src="/assets/logo.svg" width="32" height="32" class="ms-4" />
      </template>
      <v-app-bar-title text="RedPepper Console" class="text-primary" />
      <v-btn-group
        density="compact"
        class="border mx-4"
        v-if="user.user && display.width.value > 800"
      >
        <v-btn text="Agents" :to="{ name: 'agents' }" />
        <v-btn text="Commands" :to="{ name: 'commands' }" />
        <v-btn text="Data Editor" :to="{ name: 'data-editor' }" />
        <v-btn text="Events" :to="{ name: 'events' }" />
        <v-btn title="Help" icon="mdi-help" :to="{ name: 'help' }" class="px-6" />
        <v-btn title="Log out" icon="mdi-logout" :to="{ name: 'logout' }" class="px-6" />
      </v-btn-group>
      <v-menu v-if="user.user && display.width.value <= 800">
        <template #activator="{ props }">
          <v-btn icon="mdi-menu" v-bind="props" class="mx-4" />
        </template>
        <v-list class="elevation-20 border" min-width="200">
          <v-list-item :to="{ name: 'agents' }">Agents</v-list-item>
          <v-list-item :to="{ name: 'commands' }">Commands</v-list-item>
          <v-list-item :to="{ name: 'data-editor' }">Data Editor</v-list-item>
          <v-list-item :to="{ name: 'events' }">Events</v-list-item>
          <v-list-item :to="{ name: 'help' }" prepend-icon="mdi-help">Help</v-list-item>
          <v-list-item :to="{ name: 'logout' }" prepend-icon="mdi-logout">Log Out</v-list-item>
        </v-list>
      </v-menu>
      <v-btn
        v-if="!user.user"
        text="Log in"
        color="primary"
        :to="{ name: 'login' }"
        class="mx-4"
        variant="flat"
      />
    </v-app-bar>
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
      <v-divider class="mx-4" vertical />
      <span v-if="user.user">{{ user.user.username }}</span>
      <v-divider class="mx-4" vertical v-if="user.user" />
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
