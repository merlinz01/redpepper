<script setup lang="ts">
const router = useRouter()
const messages = useMessages()
const notifications = useNotifications()
const agent = ref('')
const command = ref('')
const args = ref('')
const kw = ref('')

function sendCommand() {
  let args_ = args.value
  if (!args_.startsWith('[')) {
    args_ = '[' + args_ + ']'
  }
  let kw_ = kw.value
  if (!kw_.startsWith('{')) {
    kw_ = '{' + kw_ + '}'
  }
  try {
    args_ = JSON.parse(args_)
  } catch (error) {
    notifications.post({ text: 'Failed to parse arguments: ' + error, type: 'error' })
    return
  }
  try {
    kw_ = JSON.parse(kw_)
  } catch (error) {
    notifications.post({ text: 'Failed to parse keyword arguments: ' + error, type: 'error' })
    return
  }
  const busy = messages.addMessage({ text: 'Sending command...', timeout: 0 })
  axios
    .post('/api/v1/command', {
      agent: agent.value,
      command: command.value,
      args: args_,
      kw: kw_
    })
    .then((response) => {
      if (response!.data.success) {
        // Don't show a toast for success so we don't obstruct the command form
      } else {
        throw new Error(response!.data.detail)
      }
    })
    .catch((error) => {
      if (error.response?.status == 401) {
        notifications.post({ text: 'Please log in', type: 'error' })
        router.push('/login')
        return
      }
      console.log(error)
      notifications.post({ text: 'Failed to send command: ' + error, type: 'error' })
    })
    .finally(() => {
      messages.removeMessage(busy)
    })
}
</script>

<template>
  <v-card title="Send Command:" class="ma-1 border" elevation="10">
    <v-card-text>
      <v-form @submit.prevent="sendCommand" class="d-flex flex-row align-center ga-1">
        <v-text-field
          v-model="agent"
          label="Target"
          placeholder="webserver1"
          persistent-placeholder
          variant="outlined"
          density="comfortable"
          hide-details
        />
        <v-text-field
          v-model="command"
          label="Command"
          placeholder="command"
          persistent-placeholder
          variant="outlined"
          density="comfortable"
          hide-details
        />
        <v-text-field
          v-model="args"
          label="Arguments"
          placeholder='"positional", "arguments"'
          persistent-placeholder
          variant="outlined"
          density="comfortable"
          hide-details
        />
        <v-text-field
          v-model="kw"
          label="Keyword Arguments"
          placeholder='"key": "word", "argu": "ments"'
          persistent-placeholder
          variant="outlined"
          density="comfortable"
          hide-details
        />
        <v-btn type="submit" text="Send" color="secondary" />
      </v-form>
    </v-card-text>
  </v-card>
</template>
