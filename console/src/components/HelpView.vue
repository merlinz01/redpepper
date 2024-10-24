<script setup lang="ts">
import DashboardPage from '@/components/DashboardPage.vue'
</script>
<template>
  <DashboardPage title="Help">
    <template #commandview><div></div></template>
    <p />
    <p>This is the help page for RedPepper Console.</p>
    <h3>Overview</h3>
    <p>The console consists of these views:</p>
    <ul>
      <li><strong>Home</strong>: The home page.</li>
      <li><strong>Login</strong>: A form that allows users to log in to the application.</li>
      <li><strong>Agents</strong>: A list of agents and their status.</li>
      <li><strong>Events</strong>: A live feed of events from the agents.</li>
      <li><strong>Send Command</strong>: A floating form for sending commands to the agents.</li>
      <li>
        <strong>Data Editor</strong>: A code editor that allows users to edit configuration files on
        the server.
      </li>
      <li><strong>Help</strong>: This page.</li>
    </ul>
    <h3>Login</h3>
    <p>
      To log in, enter a username and password (configured in <code>manager.yml</code>) in the form
      and click the "Log In" button.
    </p>
    <p>
      If two-factor authentication is enabled, you will be prompted to enter a code from your TOTP
      app.
    </p>
    <h3>Send Command</h3>
    <p>
      The Send Command form allows you to send commands to the agents. This form appears in some of
      the views, such as the Agents view and the Commands view.
    </p>
    <p>
      To send a command, enter the name of the targeted agent, the command, and any positional and
      keyword arguments in JSON format, and click the "Send" button. You can see the progress and
      result of the command in the Commands view.
    </p>
    <h3>Agents</h3>
    <p>
      The Agents view displays a list of agents and their status. Click the Refresh button to update
      the list.
    </p>
    <h3>Events</h3>
    <p>The Events view displays a live feed of events from the agents.</p>
    <h3>Commands</h3>
    <p>
      The Commands view displays a list of commands that have been sent to the agents. Click the
      Refresh button to update the list.
    </p>
    <h3>Data Editor</h3>
    <p>
      The Data Editor allows you to edit the configuration files that are used by the Manager to
      configure the agents.
    </p>
    <p>
      To edit a file, select it from the tree view on the left. The file will be displayed in the
      editor on the right.
    </p>
    <p>To save your changes, click the "Save" button.</p>
    <p>
      You can create, rename, and delete files and directories using the buttons above the tree
      view.
    </p>
    <p>
      The editor supports syntax highlighting and other features provided by the Ace Editor. You can
      select the syntax highlighting mode and the color theme from the dropdowns below the editor.
    </p>
    <h3>Built With</h3>
    <p>RedPepper Manager and Agent are built upon the following libraries:</p>
    <ul>
      <li>
        <a href="https://www.python.org/" target="_blank" rel="noopener noreferrer">Python</a>
        underneath it all
      </li>
      <li>
        <a href="https://github.com/python-trio/trio" target="_blank" rel="noopener noreferrer"
          >Trio</a
        >
        for asynchronous I/O and concurrency
      </li>
      <li>
        <a href="https://fastapi.tiangolo.com/" target="_blank" rel="noopener noreferrer"
          >FastAPI</a
        >
        for the REST API
      </li>
      <li>
        <a href="https://github.com/pgjones/hypercorn/" target="_blank" rel="noopener noreferrer"
          >Hypercorn</a
        >
        for the API web server
      </li>
      <li>
        <a href="https://pyyaml.org/" target="_blank" rel="noopener noreferrer">PyYAML</a>
        for configuration file parsing
      </li>
      <li>
        <a href="https://www.sqlite.org/" target="_blank" rel="noopener noreferrer">SQLite</a>
        for event storage
      </li>
      <li>
        <a
          href="https://developers.google.com/protocol-buffers/"
          target="_blank"
          rel="noopener noreferrer"
          >Protocol Buffers</a
        >
        for communication between the Manager and Agents
      </li>
      <li>
        <a
          href="https://github.com/untitaker/python-atomicwrites"
          target="_blank"
          rel="noopener noreferrer"
          >AtomicWrites</a
        >
        for safe configuration file updates
      </li>
      <li>
        <a href="https://github.com/pyotp/pyotp" target="_blank" rel="noopener noreferrer">PyOTP</a>
        for two-factor authentication
      </li>
    </ul>
    <p>RedPepper Console is built upon the following libraries:</p>
    <ul>
      <li>
        <a href="https://vuejs.org/" target="_blank" rel="noopener noreferrer">Vue 3</a>
        for a responsive web interface, along with
        <a href="https://router.vuejs.org/" target="_blank" rel="noopener noreferrer">Vue Router</a>
        and <a href="https://pinia.vuejs.org/" target="_blank" rel="noopener noreferrer">Pinia</a>.
      </li>
      <li>
        <a href="https://vuetifyjs.com/" target="_blank" rel="noopener noreferrer">Vuetify</a> for
        nice-looking UI components
      </li>
      <li>
        <a href="https://ace.c9.io/" target="_blank" rel="noopener noreferrer">Ace Editor</a>
        for a great configuration editing experience
      </li>
    </ul>
    <h3>License</h3>
    <p>
      RedPepper is licensed under the MIT License. You are free to use, modify, and distribute the
      software as long as you include the original copyright notice. See
      <a
        href="https://github.com/merlinz01/redpepper/blob/main/LICENSE.txt"
        target="_blank"
        rel="noopener noreferrer"
        >LICENSE.txt</a
      >
      for details.
    </p>
  </DashboardPage>
</template>

<style scoped>
ul,
ol,
p {
  margin: 0.5em 1em;
}

ul,
ol {
  margin-left: 2.5em;
}
h1,
h2,
h3,
h4,
h5,
h6 {
  margin-top: 1em;
  margin-bottom: 0.5em;
  color: rgb(var(--v-theme-secondary));
}
</style>
