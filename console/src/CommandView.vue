<script setup lang="ts">
import { useRouter } from 'vue-router'
import Fetch from './fetcher'
import { useToast } from './toast'

const router = useRouter()
const toast = useToast()

function sendCommand(event: any) {
  event.preventDefault()
  const agent = (document.getElementById('command-agent')! as HTMLInputElement).value
  const command = (document.getElementById('command-command')! as HTMLInputElement).value
  let args = (document.getElementById('command-args')! as HTMLInputElement).value
  if (!args.startsWith('[')) {
    args = '[' + args + ']'
  }
  let kw = (document.getElementById('command-kw')! as HTMLInputElement).value
  if (!kw.startsWith('{')) {
    kw = '{' + kw + '}'
  }
  try {
    args = JSON.parse(args)
  } catch (error) {
    toast.new('Failed to parse arguments: ' + error, 'error')
    return
  }
  try {
    kw = JSON.parse(kw)
  } catch (error) {
    toast.new('Failed to parse keyword arguments: ' + error, 'error')
    return
  }
  const busy = toast.new('Sending command...', 'info')
  Fetch('/api/v1/command')
    .onError((error: any) => {
      busy.close()
      console.log(error)
      toast.new('Failed to send command: ' + error, 'error')
    })
    .onStatus(401, () => {
      busy.close()
      toast.new('Please log in', 'error')
      router.push('/login')
    })
    .onSuccess((data: any) => {
      if (data.success) {
        busy.close()
        // Don't show a toast for success so we don't obstruct the command form
      } else {
        throw new Error(data.detail)
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
  document.getElementById('command-form')!.classList.toggle('cf-shown')
  if (document.getElementById('command-form')!.classList.contains('cf-shown')) {
    document.getElementById('command-agent')!.focus()
  }
}
</script>

<template>
  <form
    id="command-form"
    class="bordered rounded lightly-padded centered justify-centered gapped wrappable row"
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
    <input type="text" id="command-agent" name="agent" placeholder="Target" />
    <input type="text" id="command-command" name="command" placeholder="Command" />
    <input type="text" id="command-args" name="args" placeholder='"positional", "arguments"' />
    <input type="text" id="command-kw" name="kw" placeholder='"key": "word", "argu": "ments"' />
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
  max-width: calc(100vw - 2rem);
}

#command-form:not(.cf-shown) *:not(#command-form-toggle-show) {
  display: none;
}
</style>
