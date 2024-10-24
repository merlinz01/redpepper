<script setup lang="ts">
import { VOtpInput } from 'vuetify/components'

const router = useRouter()
const notifications = useNotifications()
const messages = useMessages()
const input = ref<VOtpInput>()
const totp = ref('')
const iserror = ref(false)

onMounted(() => {
  input.value!.focus()
})

function verifyTOTP() {
  const busy = messages.addMessage({ text: 'Verifying TOTP...', timeout: 0 })
  axios
    .post('/api/v1/verify_totp', {
      totp: totp.value
    })
    .then((response) => {
      if (response!.data.success) {
        notifications.post({ text: 'Logged in.', type: 'success' })
        router.push('/agents')
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
      iserror.value = true
      notifications.post({ text: 'Failed to verify TOTP: ' + error, type: 'error' })
    })
    .finally(() => {
      messages.removeMessage(busy)
      totp.value = ''
    })
}

function verify_totp_when_done() {
  iserror.value = false
  if (totp.value.length === 6) {
    verifyTOTP()
  }
}
</script>

<template>
  <v-form @submit.prevent="verifyTOTP">
    <v-card max-width="500" title="Verify 2FA" class="mx-auto my-2">
      <v-card-text class="d-flex flex-column ga-4">
        <v-label>Enter the 6-digit code from your authenticator app:</v-label>
        <v-otp-input
          id="totp"
          class="mt-4"
          v-model="totp"
          @input="verify_totp_when_done"
          placeholder="X"
          :error="iserror"
          autofocus
          ref="input"
        />
      </v-card-text>
      <v-card-actions>
        <v-btn type="submit" color="primary" text="Verify" variant="elevated" class="mx-auto" />
      </v-card-actions>
    </v-card>
  </v-form>
</template>
