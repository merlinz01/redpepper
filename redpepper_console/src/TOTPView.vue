<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Fetch from './fetcher'
import { Alert } from './dialogs'

const router = useRouter()
const totp = ref('')

onMounted(() => {
  document.getElementById('totp').focus()
})

function submitLogin(event) {
  if (event) {
    event.preventDefault()
  }
  const totp_input = document.getElementById('totp')
  Fetch('/api/v1/verify_totp')
    .onError((error) => {
      console.log(error)
      Alert(error).title('Failed to verify TOTP').showModal()
    })
    .onStatus(401, () => {
      console.log('Unauthorized. Redirecting to login page.')
      router.push('/login')
    })
    .onSuccess((data) => {
      if (data.success) {
        router.push('/agents')
      } else {
        throw new Error(data.detail)
      }
    })
    .credentials('same-origin')
    .post({
      totp: totp_input.value
    })
  totp_input.value = ''
}

function verify_totp_when_6digit() {
  if (document.getElementById('totp').value.length === 6) {
    submitLogin(null)
  }
}
</script>

<template>
  <form id="totp-view" @submit="submitLogin" class="padded gapped centered column">
    <h3>Enter TOTP</h3>
    <label for="username">Six-digit code from your authenticator app:</label>
    <input
      type="text"
      id="totp"
      name="totp"
      class="text-centered"
      required
      placeholder="XXXXXX"
      minlength="6"
      maxlength="6"
      :value="totp"
      @input="verify_totp_when_6digit"
      style="width: 6em"
    />
    <div class="gapped row">
      <button type="submit">Verify</button>
      <button type="button" @click="router.push('/login')">Back</button>
    </div>
  </form>
</template>
