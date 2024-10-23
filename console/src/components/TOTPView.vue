<script setup lang="ts">
import Fetch from '@/fetcher'
import { VOtpInput } from 'vuetify/components'
import useNotifications from '@/stores/notifications'
import useMessages from '@/stores/messages'

const router = useRouter()
const notifications = useNotifications()
const messages = useMessages()
const input = ref<VOtpInput>()
const totp = ref('')
const iserror = ref(false)

onMounted(() => {
  input.value!.focus()
})

function submitLogin() {
  const busy = messages.addMessage({ text: 'Verifying TOTP...', timeout: 0 })
  Fetch('/api/v1/verify_totp')
    .onError((error: any) => {
      iserror.value = true
      console.log(error)
      notifications.post({ text: 'Failed to verify TOTP: ' + error, type: 'error' })
    })
    .onStatus(401, () => {
      console.log('Unauthorized. Redirecting to login page.')
      router.push('/login')
    })
    .onSuccess((data: any) => {
      if (data.success) {
        notifications.post({ text: 'Logged in.', type: 'success' })
        router.push('/agents')
      } else {
        throw new Error(data.detail)
      }
    })
    .credentials('same-origin')
    .post({
      totp: totp.value
    })
    .finally(() => {
      messages.removeMessage(busy)
      totp.value = ''
    })
}

function verify_totp_when_done() {
  iserror.value = false
  if (totp.value.length === 6) {
    submitLogin()
  }
}
</script>

<template>
  <v-form @submit.prevent="submitLogin">
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
