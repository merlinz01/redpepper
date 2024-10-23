<script setup lang="ts">
import Fetch from '@/fetcher'
import useNotifications from '@/stores/notifications'
import useMessages from '@/stores/messages'

const router = useRouter()
const notifications = useNotifications()
const messages = useMessages()
const username = ref('')
const password = ref('')

onMounted(() => {
  document.getElementById('username')!.focus()
})

function submitLogin() {
  const busy = messages.addMessage({ text: 'Logging in...', timeout: 0 })
  Fetch('/api/v1/login')
    .onError((error: any) => {
      console.log(error)
      notifications.post({ text: 'Failed to log in: ' + error, type: 'error', id: 'login.failed' })
    })
    .onSuccess((data: any) => {
      if (data.success) {
        messages.addMessage({ text: 'Logged in. Please complete 2FA.', type: 'success' })
        router.push('/totp')
      } else {
        throw new Error(data.detail)
      }
    })
    .credentials('same-origin')
    .post({
      username: username.value,
      password: password.value
    })
    .finally(() => {
      messages.removeMessage(busy)
      password.value = ''
    })
}
</script>

<template>
  <v-form @submit.prevent="submitLogin">
    <v-card max-width="500" title="Log in" class="mx-auto my-2">
      <v-card-text class="d-flex flex-column ga-4">
        <v-text-field
          label="Username"
          id="username"
          name="username"
          variant="outlined"
          required
          persistent-placeholder
          class="mt-4"
          :rules="[(v) => !!v || 'Username is required']"
          v-model="username"
        />
        <v-text-field
          label="Password"
          type="password"
          name="password"
          variant="outlined"
          required
          persistent-placeholder
          class="mb-n4"
          :rules="[(v) => !!v || 'Password is required']"
          v-model="password"
        />
      </v-card-text>
      <v-card-actions>
        <v-btn type="submit" color="primary" text="Log in" variant="elevated" class="mx-auto" />
      </v-card-actions>
    </v-card>
  </v-form>
</template>
