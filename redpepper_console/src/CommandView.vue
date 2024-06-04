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
      alert('Failed to send command: ' + error)
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
</script>

<template>
  <form
    id="command-form"
    class="lightly-padded centered justify-centered gapped wrappable row"
    @submit="sendCommand"
  >
    <h3>Send Command:</h3>
    <input type="text" id="agent" name="agent" placeholder="Agent" />
    <input type="text" id="command" name="command" placeholder="Command" />
    <input type="text" id="args" name="args" placeholder='["command", "arguments"]' />
    <input type="text" id="kw" name="kw" placeholder='{"key": "value"}' />
    <button type="submit">Send</button>
  </form>
</template>

<style scoped>
#command-form {
  position: fixed;
  top: 4.5rem;
  background: var(--color-background);
  border-bottom: 1px dotted var(--color-border);
}
form h3 {
  margin: 0;
}
</style>
