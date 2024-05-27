<script setup></script>

<template>
  <div id="help-view" class="padded">
    <h1>Help</h1>
    <p>This is the help page for RedPepper Console.</p>
    <h2>Overview</h2>
    <p>The console consists of these views:</p>
    <ul>
      <li><strong>Home</strong>: The default view that displays a welcome message.</li>
      <li><strong>Login</strong>: A form that allows users to log in to the application.</li>
      <li><strong>Agents</strong>: A list of agents and their status.</li>
      <li><strong>Events</strong>: A live feed of events from the agents.</li>
      <li>
        <strong>Commands</strong>: A form included in the Agents and Events views to send commands
        to the agents.
      </li>
      <li>
        <strong>Data Editor</strong>: A text editor that allows users to edit configuration files on
        the server.
      </li>
      <li><strong>Help</strong>: This page.</li>
    </ul>
    <h2>Login</h2>
    <p>
      To log in, enter a username and password (configured in <code>manager.yml</code>) in the form
      and click the "Log In" button.
    </p>
    <p>
      If two-factor authentication is enabled, you will be prompted to enter a code from your TOTP
      app.
    </p>
    <h2>Built with</h2>
    <ul>
      <li>
        <a href="https://v3.vuejs.org/" target="_blank" rel="noopener noreferrer">Vue.js 3</a>
      </li>
      <li>
        <a href="https://router.vuejs.org/" target="_blank" rel="noopener noreferrer">Vue Router</a>
      </li>
      <li>
        <a href="https://ace.c9.io/" target="_blank" rel="noopener noreferrer">Ace Editor</a>
      </li>
    </ul>
    <h2>License</h2>
    <p>
      RedPepper Console is licensed under the MIT License. You are free to use, modify, and
      distribute the software as long as you include the original copyright notice.
    </p>
  </div>
</template>

<style scoped></style>
