<script setup>
import { ref } from 'vue'

const theme = ref('dark')
const toggleTheme = () => {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
}
</script>

<template>
  <div id="app" :data-theme="theme">
    <header id="header" class="lightly-padded gapped bottom-aligned row">
      <img
        id="header-logo"
        alt="RedPepper logo"
        class="logo"
        src="./assets/logo.svg"
        width="48"
        height="48"
      />
      <h1 id="header-title">RedPepper</h1>
      <nav id="header-nav" class="gapped row">
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/login">Login</RouterLink>
        <RouterLink to="/agents">Agents</RouterLink>
        <RouterLink to="/events">Events</RouterLink>
        <RouterLink to="/data">Data Editor</RouterLink>
        <RouterLink to="/logout">Logout</RouterLink>
        <RouterLink to="/help">Help</RouterLink>
      </nav>
      <button id="header-toggle-theme" @click="toggleTheme">Toggle Theme</button>
    </header>

    <main>
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
#header {
  border-bottom: 1px solid var(--color-border);
}

#header-title {
  color: var(--color-redpepper);
  margin: 0.25rem 1rem;
}

#header-toggle-theme {
  margin-left: auto;
}

#app {
  height: 100%;
}

main {
  overflow-y: auto;
  height: calc(100% - 5rem);
}
</style>
