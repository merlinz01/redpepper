<script setup>
function toggleTheme() {
  document.getElementById('app').classList.add('theme-transition')
  if (document.documentElement.getAttribute('data-theme') === 'dark') {
    document.documentElement.setAttribute('data-theme', 'light')
  } else {
    document.documentElement.setAttribute('data-theme', 'dark')
  }
  setTimeout(() => {
    document.getElementById('app').classList.remove('theme-transition')
  }, 1000)
}
</script>

<template>
  <div id="app" class="full-height">
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
    <main class="full-height">
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
}

#header-title {
  color: var(--color-redpepper);
  margin: 0.25rem 1rem;
}

#header-toggle-theme {
  margin-left: auto;
}

#app {
  background: var(--color-background);
  padding-top: 4rem;
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
