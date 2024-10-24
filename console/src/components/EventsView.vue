<script setup lang="ts">
import dayjs from 'dayjs'
import DashboardPage from '@/components/DashboardPage.vue'

const connecting = ref(true)
const logs = ref<any[]>([])
const messages = useMessages()

const ws = ref<WebSocket | null>(null)

const numRetries = ref(0)

function clear() {
  logs.value = []
}

function formatDate(date: number) {
  date = date * 1000
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

function getStyle(log: any) {
  if (log.type === 'command') {
    return 'color: var(--color-blue);'
  } else if (log.type === 'command_result') {
    if (log.status == 1) {
      return 'color: var(--color-green);'
    } else if (log.status == 2) {
      return 'color: var(--color-red);'
    } else if (log.status == 3) {
      return 'color: var(--color-orange);'
    } else {
      return 'color: var(--color-blue);'
    }
  } else if (log.type === 'command_progress') {
    return 'color: var(--color-blue);'
  } else if (log.type === 'auth_success') {
    return 'color: var(--color-purple);'
  } else if (log.type === 'auth_failure') {
    return 'color: var(--color-red);'
  } else if (log.type == 'disconnected') {
    return 'color: var(--color-orange);'
  } else if (log.type == 'connected') {
    return 'color: var(--color-brown);'
  } else {
    return ''
  }
}

function connect() {
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
      connecting.value = false
    }
    return
  }
  const busy = messages.addMessage({ text: 'Connecting to WebSocket...', id: 'events.ws' })
  ws.value = new WebSocket('/api/v1/events/ws')
  ws.value.onopen = () => {
    messages.removeMessage(busy)
    connecting.value = false
    numRetries.value = 0
  }
  ws.value.onmessage = (event) => {
    const data = JSON.parse(event.data)
    logs.value.unshift(data)
  }
  ws.value.onerror = (event) => {
    messages.removeMessage(busy)
    messages.addMessage({ text: 'Failed to connect to WebSocket.', type: 'error', id: 'events.ws' })
  }
  ws.value.onclose = () => {
    console.log('WebSocket closed')
    connecting.value = true
    ws.value = null
    setTimeout(() => {
      connect()
    }, 2000)
  }
}

onMounted(() => {
  numRetries.value = 0
  connect()
})

onUnmounted(() => {
  if (ws.value) {
    ws.value.onclose = null
    ws.value.close()
  }
})
</script>

<template>
  <DashboardPage title="Events">
    <h1 class="d-flex flex-row">
      <div v-text="ws && ws.readyState == ws.OPEN ? '\u2714' : '\u2716'"></div>
      <div class="spinner" v-show="connecting"></div>
    </h1>
    <div class="d-flex flex-row">
      <v-btn type="button" @click="clear">Clear</v-btn>
    </div>
    <v-table>
      <thead>
        <tr>
          <th style="width: 20%">Time</th>
          <th style="width: 20%">Agent</th>
          <th style="width: 20%">Event</th>
          <th>Data</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in logs" :key="log.id" :style="getStyle(log)">
          <td>{{ formatDate(log.time) }}</td>
          <td>{{ log.agent || '(N/A)' }}</td>
          <td>{{ log.type }}</td>
          <td><pre v-text="JSON.stringify(log)" class="text-wrap" /></td>
        </tr>
      </tbody>
    </v-table>
  </DashboardPage>
</template>

<style scoped>
.command-output {
  color: var(--color-text);
}
</style>
