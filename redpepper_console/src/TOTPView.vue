<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
const router = useRouter()
const totp = ref('')
onMounted(() => {
  document.getElementById('totp').focus()
})

const submitLogin = (event) => {
  if (event) {
    event.preventDefault()
  }
  const totp_input = document.getElementById('totp')
  fetch('/api/v1/verify_totp', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'same-origin',
    body: JSON.stringify({
      totp: totp_input.value
    })
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        router.push('/agents')
      } else {
        alert('Verification failed!')
      }
    })
    .catch((error) => {
      alert('Verification failed: ' + error)
      console.log(error)
      router.push('/login')
    })
  totp_input.value = ''
}

const verify_totp_on_change = () => {
  const totp = document.getElementById('totp').value
  if (totp.length === 6) {
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
      placeholder="XXXXXXX"
      minlength="6"
      maxlength="6"
      :value="totp"
      @input="verify_totp_on_change"
      style="width: 6em"
    />
    <div class="gapped row">
      <button type="submit">Verify</button>
      <button type="button" @click="router.push('/login')">Back</button>
    </div>
  </form>
</template>
