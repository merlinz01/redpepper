<script setup lang="ts">
const router = useRouter()
const notifications = useNotifications()
const messages = useMessages()
const username = ref('')
const password = ref('')
const user = useUser()

onMounted(() => {
  document.getElementById('username')!.focus()
})

function submitLogin() {
  const busy = messages.addMessage({ text: 'Logging in...', timeout: 0 })
  axios
    .post('/api/v1/login', {
      username: username.value,
      password: password.value
    })
    .then((response) => {
      if (response!.data.success) {
        messages.addMessage({ text: 'Logged in. Please complete 2FA.', type: 'success' })
        router.push('/totp')
        user.user = { username: username.value }
      } else {
        throw new Error(response!.data.detail)
      }
    })
    .catch((error) => {
      notifications.post({ text: 'Failed to log in: ' + error, type: 'error', id: 'login.failed' })
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
