<script setup lang="ts">
import { onMounted } from 'vue'
import CommandView from './CommandView.vue'

function toggleTheme() {
  document.getElementById('app')!.classList.add('theme-transition')
  var preferredTheme = document.documentElement.getAttribute('data-theme')
  if (preferredTheme === 'dark') {
    preferredTheme = 'light'
  } else {
    preferredTheme = 'dark'
  }
  document.documentElement.setAttribute('data-theme', preferredTheme)
  localStorage.setItem('colorTheme', preferredTheme)
  setTimeout(() => {
    document.getElementById('app')!.classList.remove('theme-transition')
  }, 1000)
}

onMounted(() => {
  var preferredTheme = localStorage.getItem('colorTheme')
  if (!preferredTheme) {
    preferredTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    localStorage.setItem('colorTheme', preferredTheme)
  }
  document.documentElement.setAttribute('data-theme', preferredTheme)
})
</script>

<template>
  <CommandView />
  <div id="app" class="full-height">
    <header id="header" class="lightly-padded gapped bottom-aligned left-justified row">
      <img id="header-logo" alt="RedPepper logo" src="./assets/logo.svg" width="32" height="32" />
      <h1 id="header-title">RedPepper</h1>
      <nav id="header-nav" class="gapped row">
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/login">Login</RouterLink>
        <RouterLink to="/agents">Agents</RouterLink>
        <RouterLink to="/events">Events</RouterLink>
        <RouterLink to="/commands">Commands</RouterLink>
        <RouterLink to="/data">Data Editor</RouterLink>
        <RouterLink to="/logout">Logout</RouterLink>
        <RouterLink to="/help">Help</RouterLink>
      </nav>
      <button id="header-toggle-theme" @click="toggleTheme">Toggle Theme</button>
    </header>
    <main class="full-height well-padded">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
#header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: var(--color-background-accent);
  z-index: 1000;
  border-bottom: 1px solid var(--color-border);
  overflow-x: auto;
  white-space: nowrap;
}

#header-title {
  color: var(--color-redpepper);
  margin: 0;
}

@media (max-width: 880px) {
  #header-title {
    display: none;
  }
}

@media (max-width: 720px) {
  #header-toggle-theme {
    position: fixed;
    top: calc(100vh - 3rem);
    right: 1rem;
    z-index: 1000;
  }
}

@media (max-width: 590px) {
  #header-nav:is(:not(:last-child)) {
    margin-left: 0;
    margin-right: 0;
  }
}

@media (max-width: 560px) {
  #header-logo {
    display: none;
  }
}
#header-nav {
  margin: 0 1rem;
}

#header-toggle-theme {
  margin-left: auto;
}

#app {
  background: var(--color-background);
  padding-top: 4rem;
  overflow: auto;
}

#app.theme-transition,
#app.theme-transition *,
#app.theme-transition *::before,
#app.theme-transition *::after {
  transition:
    color 1s,
    border-color 1s,
    background-color 1s;
}
</style>
