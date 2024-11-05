<script setup lang="ts">
import dayjs from 'dayjs'
import DashboardPage from '@/components/DashboardPage.vue'
import CommandView from './CommandForm.vue'

const router = useRouter()
const route = useRoute()
const messages = useMessages()
const notifications = useNotifications()
const commands = ref<any[]>([])
const ws = ref<WebSocket | null>(null)
const numRetries = ref(0)
const connection_status = ref('')

function refresh() {
  const busy = messages.addMessage({ text: 'Fetching latest commands...', id: 'commands.fetching' })
  axios
    .get('/api/v1/commands/last', { params: { max: 20 } })
    .then((response) => {
      commands.value = response!.data.commands
    })
    .catch((error) => {
      if (error.response?.status == 401) {
        notifications.post({ text: 'Please log in', type: 'error' })
        router.push('/login')
        return
      }
      commands.value = []
      notifications.post({ text: 'Failed to fetch commands: ' + error, type: 'error' })
    })
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
    if (
      confirm(
        'Retried WebSocket connection 10 times. Continue?\n' +
          'If not, you will have to refresh the page before you can get real-time updates.'
      )
    ) {
      numRetries.value = 0
      connect()
    } else {
      messages.addMessage({
        text: 'Failed to connect to WebSocket. Please check your network connection and refresh the page.',
        type: 'error',
        id: 'commands.connect_failed',
        timeout: 0
      })

      connection_status.value = '\u2716' // X
    }
    return
  }
  connection_status.value = '\u231B' // hourglass
  const busy = messages.addMessage({ text: 'Connecting to WebSocket...', id: 'commands.ws' })
  ws.value = new WebSocket('/api/v1/events/ws')
  ws.value.addEventListener('open', () => {
    messages.removeMessage(busy)
    connection_status.value = '\u2714' // check mark
    numRetries.value = 0
  })
  ws.value.onmessage = (event) => {
    const data = JSON.parse(event.data)
    handleEvent(data)
  }
  ws.value.onerror = (event) => {
    messages.removeMessage(busy)
    notifications.post({
      text: 'Failed to connect to WebSocket: ' + event,
      type: 'error',
      id: 'commands.ws'
    })
  }
  ws.value.onclose = () => {
    console.log('WebSocket closed')
    connection_status.value = '\u2716' // X
    ws.value = null
    setTimeout(() => {
      connect()
    }, 1000)
  }
}

onMounted(() => {
  numRetries.value = 0
  connection_status.value = '\u231B' // hourglass
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
    <template #after_title>
      <div>{{ connection_status }}</div>
    </template>
    <CommandView :initial-agent="route.query.agent as string" />
    <v-divider class="my-2" />
    <v-card title="Command History">
      <v-card-text>
        <v-table class="table-layout-fixed" density="compact">
          <thead>
            <tr>
              <th style="width: 35%">Command</th>
              <th style="width: 70%">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="command in commands" :key="command.id">
              <td>
                <div class="d-flex flex-column my-2">
                  <span class="font-small text-primary">{{ command.id }}</span>
                  <span>at {{ formatDate(command.time) }}</span>
                  <span class="text-secondary">{{ command.agent }}</span>
                  <code class="bg-surface-light px-2 py-1 rounded">
                    {{ command.command.command }}
                    {{
                      {
                        args: command.command.args.length ? command.command.args : undefined,
                        ...command.command.kw
                      }
                    }}
                  </code>
                </div>
              </td>
              <td>
                <div class="d-flex flex-column align-center ga-1 my-2">
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
                    class="border rounded overflow-x-auto w-100 ma-1 pa-2"
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
      </v-card-text>
    </v-card>
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
<style>
.table-layout-fixed table {
  table-layout: fixed;
}
</style>
