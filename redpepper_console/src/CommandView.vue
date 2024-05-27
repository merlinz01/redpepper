<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const sendCommand = (event) => {
  event.preventDefault()
  const agent = document.getElementById('agent').value
  const command = document.getElementById('command').value
  let args = document.getElementById('args').value
  let kw = document.getElementById('kw').value
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
  fetch('https://localhost:8080/api/v1/command', {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      agent: agent,
      command: command,
      args: args,
      kw: kw
    })
  })
    .then((response) => {
      if (response.status == 401) {
        router.push('/login')
        return
      }
      if (!response.ok) {
        throw new Error('Failed to send command')
      }
      response.json().then((data) => {
        if (data.success) {
          console.log('Command sent!')
          if (router.currentRoute.value.path != '/events') {
            router.push('/events')
          }
        } else {
          alert('Command failed: ' + data.detail)
        }
      })
    })
    .catch((error) => {
      console.log(error)
      alert(error)
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
