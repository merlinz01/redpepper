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
    <h2>Agents</h2>
    <p>
      The Agents view displays a list of agents and their status. Click the Refresh button to update
      the list.
    </p>
    <h2>Events</h2>
    <p>The Events view displays a live feed of events from the agents.</p>
    <p>
      This page initiates a WebSocket connection to the server to receive events in real-time. The
      Refresh button updates the list of events since the date and time specified in the input
      beside it.
    </p>
    <h2>Commands</h2>
    <p>
      The Commands form allows you to send commands to the agents. This form appears on the Agents
      and Events pages.
    </p>
    <p>
      To send a command, enter the name of the targeted agent, the command, and any positional and
      keyword arguments in JSON format, and click the "Send" button. You can see the progress and
      result of the command in the Events view.
    </p>
    <h2>Data Editor</h2>
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
    <h2>Built With</h2>
    <p>RedPepper Manager and Agent are built upon the following wonderful libraries:</p>
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
        for the web server
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
    <p>RedPepper Console is built upon the following wonderful libraries:</p>
    <ul>
      <li>
        <a href="https://v3.vuejs.org/" target="_blank" rel="noopener noreferrer">Vue.js 3</a>
        for a responsive web interface
      </li>
      <li>
        <a href="https://router.vuejs.org/" target="_blank" rel="noopener noreferrer">Vue Router</a>
        to keep it all under one roof
      </li>
      <li>
        <a href="https://ace.c9.io/" target="_blank" rel="noopener noreferrer">Ace Editor</a>
        for a great configuration editing experience
      </li>
    </ul>
    <h2>License</h2>
    <p>
      RedPepper Console is licensed under the MIT License. You are free to use, modify, and
      distribute the software as long as you include the original copyright notice. See
      <a
        href="https://github.com/merlinz01/redpepper/blob/main/LICENSE.txt"
        target="_blank"
        rel="noopener noreferrer"
        >LICENSE.txt</a
      >
      for details.
    </p>
    <h2>Author</h2>
    <p>
      <a href="https://github.com/merlinz01" target="_blank" rel="noopener noreferrer">
        Merlin Zimmerman
      </a>
    </p>
  </div>
</template>

<style scoped></style>
