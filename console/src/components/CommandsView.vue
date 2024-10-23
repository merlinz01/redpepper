<script setup lang="ts">
import dayjs from 'dayjs'
import Fetch from '@/fetcher'
import { Confirm } from '@/dialogs'
import DashboardPage from '@/components/DashboardPage.vue'
import useMessages from '@/stores/messages'
import useNotifications from '@/stores/notifications'

const router = useRouter()
const messages = useMessages()
const notifications = useNotifications()
const commands = ref<any[]>([])
const ws = ref<WebSocket | null>(null)
const numRetries = ref(0)

function refresh() {
  const busy = messages.addMessage({ text: 'Fetching latest commands...', id: 'commands.fetching' })
  Fetch('/api/v1/commands/last')
    .query('max', 20)
    .onError((error: any) => {
      commands.value = []
      notifications.post({ text: 'Failed to fetch commands: ' + error, type: 'error' })
    })
    .onStatus(401, () => {
      notifications.post({ text: 'Please log in', type: 'error' })
      router.push('/login')
    })
    .onSuccess((data: any) => {
      commands.value = data.commands
    })
    .credentials('same-origin')
    .get()
    .finally(() => {
      messages.removeMessage(busy)
    })
}

function handleEvent(data: any) {
  if (data.type === 'command') {
    data = {
      id: data.id,
      time: data.time,
      agent: data.agent,
      command: { command: data.command, args: data.args, kw: data.kw },
      progress_current: 0,
      progress_total: undefined,
      status: 0,
      output: ''
    }
    commands.value.unshift(data)
  } else if (data.type === 'command_progress') {
    const command = commands.value.find((command) => command.id === data.id)
    if (command) {
      command.progress_current = data.progress_current
      command.progress_total = data.progress_total
      command.output = data.message
    } else {
      data.agent = 'Unknown'
      data.command = { command: 'Unknown', args: 'Unknown', kw: 'Unknown' }
      data.status = 0
      data.output = data.message
      commands.value.unshift(data)
    }
  } else if (data.type === 'command_result') {
    const command = commands.value.find((command) => command.id === data.id)
    if (command) {
      command.status = data.status
      command.output = data.output
    } else {
      data.agent = 'Unknown'
      data.command = { command: 'Unknown', args: 'Unknown', kw: 'Unknown' }
      data.progress_current = 0
      data.progress_total = undefined
      commands.value.unshift(data)
    }
  }
}

function formatDate(date: number) {
  date = date * 1000
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

function getStatusText(status: number) {
  if (status === 0) {
    return 'Pending'
  } else if (status === 1) {
    return 'Succeeded'
  } else if (status === 2) {
    return 'Failed'
  } else if (status === 3) {
    return 'Canceled'
  } else {
    return status
  }
}

function getProgress(command: any) {
  if (command.progress_total == undefined) {
    return 0
  }
  if (command.progress_total == 0) {
    return 100
  }
  return (command.progress_current / command.progress_total) * 100
}

function getBackground(command: any) {
  if (command.status === 0) {
    // Pending
    return 'info'
  } else if (command.status === 1) {
    // Success
    return 'success'
  } else if (command.status === 2) {
    // Failed
    return 'error'
  } else if (command.status === 3) {
    // Canceled
    return 'warning'
  } else {
    return 'info'
  }
}
function connect() {
  if (ws.value) {
    ws.value!.close()
  }
  numRetries.value++
  if (numRetries.value >= 10) {
    Confirm('If not, you will have to refresh the page before you can get real-time updates.')
      .title('Retried WebSocket connection 10 times. Continue?')
      .onConfirm(() => {
        numRetries.value = 0
        connect()
      })
      .onCancel(() => {
        messages.addMessage({
          text: 'Failed to connect to WebSocket. Please check your network connection and refresh the page.',
          type: 'error',
          id: 'commands.connect_failed',
          timeout: 0
        })

        document.getElementById('connection_spinner')!.classList.add('hidden')
      })
      .showModal()
    return
  }
  const busy = messages.addMessage({ text: 'Connecting to WebSocket...', id: 'commands.ws' })
  ws.value = new WebSocket('/api/v1/events/ws')
  ws.value.addEventListener('open', () => {
    messages.removeMessage(busy)
    document.getElementById('connection_spinner')!.classList.add('hidden')
    document.getElementById('connection_status')!.textContent = '\u2714'
    numRetries.value = 0
  })
  ws.value.onmessage = (event) => {
    const data = JSON.parse(event.data)
    handleEvent(data)
  }
  ws.value.onerror = (event) => {
    console.log(event)
    messages.removeMessage(busy)
    notifications.post({
      text: 'Failed to connect to WebSocket.',
      type: 'error',
      id: 'commands.ws'
    })
  }
  ws.value.onclose = () => {
    console.log('WebSocket closed')
    const spinner = document.getElementById('connection_spinner')
    if (spinner) {
      spinner.classList.remove('hidden')
    }
    const status = document.getElementById('connection_status')
    if (status) {
      status.textContent = '\u2716'
    }
    ws.value = null
    setTimeout(() => {
      connect()
    }, 1000)
  }
}

onMounted(() => {
  numRetries.value = 0
  document.getElementById('connection_spinner')!.classList.remove('hidden')
  document.getElementById('connection_status')!.textContent = '\u231B'
  connect()
  refresh()
})

onUnmounted(() => {
  if (ws.value) {
    ws.value.onclose = null
    ws.value.close()
  }
  messages.removeMessage('commands.connect_failed')
})
</script>

<template>
  <DashboardPage title="Commands">
    <h1 class="d-flex flex-row">
      <div id="connection_status" style="color: var(--color-gray)"></div>
      <div class="spinner hidden" id="connection_spinner"></div>
    </h1>
    <v-table>
      <thead>
        <tr>
          <th style="width: 30%; min-width: 20em">Command</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="command in commands" :key="command.id">
          <td>
            <div class="d-flex flex-column">
              <span>Command ID: {{ command.id }}</span>
              <span>Time: {{ formatDate(command.time) }}</span>
              <span>Agent: {{ command.agent }}</span>
              <span>Command: {{ command.command.command }}</span>
              <span>Arguments: {{ command.command.args }}</span>
              <span>Parameters: {{ command.command.kw }}</span>
            </div>
          </td>
          <td>
            <div class="d-flex flex-column align-center ga-1">
              <span>
                {{ getStatusText(command.status) }} {{ command.progress_current || 0 }} /
                {{ command.progress_total || 0 }}
              </span>
              <v-progress-linear
                :model-value="getProgress(command)"
                :color="getBackground(command)"
                height="20"
                rounded
                rounded-bar
                :striped="command.status === 0"
              />
              <pre
                class="border rounded overflow-x-auto w-100"
                v-if="command.status !== 0"
                style="max-height: 2.5em; overflow: hidden; cursor: pointer; max-width: 750px"
                @click="
                  (event: any) => {
                    event.target.style.maxHeight = null
                    event.target.style.overflow = null
                    event.target.style.cursor = null
                  }
                "
                @dblclick="
                  (event: any) => {
                    event.target.style.maxHeight = '2.5em'
                    event.target.style.overflow = 'hidden'
                    event.target.style.cursor = 'pointer'
                  }
                "
                >{{ command.output }}</pre
              >
              <span v-else>{{ command.output || 'No output' }}</span>
            </div>
          </td>
        </tr>
      </tbody>
    </v-table>
  </DashboardPage>
</template>

<style scoped>
tbody tr {
  animation: fade-in 0.5s;
}
@keyframes fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
