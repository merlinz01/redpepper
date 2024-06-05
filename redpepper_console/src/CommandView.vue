<script setup>
import { useRouter } from 'vue-router'
import Fetch from './fetcher'

const router = useRouter()

function sendCommand(event) {
  event.preventDefault()
  const agent = document.getElementById('agent').value
  const command = document.getElementById('command').value
  let args = document.getElementById('args').value || '[]'
  let kw = document.getElementById('kw').value || '{}'
  try {
    args = JSON.parse(args)
  } catch (error) {
    alert('Failed to parse arguments: ' + error)
    return
  }
  try {
    kw = JSON.parse(kw)
  } catch (error) {
    alert('Failed to parse keyword arguments: ' + error)
    return
  }
  Fetch('/api/v1/command')
    .onError((error) => {
      alert('Failed to send command:\n' + error)
    })
    .onStatus(401, () => {
      console.log('Unauthorized. Redirecting to login page.')
      router.push('/login')
    })
    .onSuccess((data) => {
      if (data.success) {
        console.log('Command sent!')
        if (router.currentRoute.value.path != '/events') {
          router.push('/events')
        }
      } else {
        alert('Command failed: ' + data.detail)
      }
    })
    .credentials('same-origin')
    .post({
      agent: agent,
      command: command,
      args: args,
      kw: kw
    })
}

function toggleShowCommandForm() {
  document.getElementById('command-form').classList.toggle('cf-shown')
}
</script>

<template>
  <form
    id="command-form"
    class="bordered rounded lightly-padded centered justify-centered gapped row"
    @submit="sendCommand"
  >
    <button
      type="button"
      @click="toggleShowCommandForm"
      id="command-form-toggle-show"
      class="bold-font"
    >
      $ _
    </button>
    <h3 class="no-margin">Send Command:</h3>
    <input type="text" id="agent" name="agent" placeholder="Target" />
    <input type="text" id="command" name="command" placeholder="Command" />
    <input type="text" id="args" name="args" placeholder='["positional", "arguments"]' />
    <input type="text" id="kw" name="kw" placeholder='{"keyword": "arguments"}' />
    <button type="submit">Send</button>
  </form>
</template>

<style scoped>
#command-form {
  position: absolute;
  bottom: 1rem;
  left: 1rem;
  background: var(--color-background-accent);
  z-index: 1000;
  box-shadow: 0 0 0.5rem rgba(0, 0, 0, 0.5);
}

#command-form:not(.cf-shown) *:not(#command-form-toggle-show) {
  display: none;
}
</style>
