<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
const router = useRouter()

onMounted(() => {
  document.getElementById('username').focus()
})

const submitLogin = (event) => {
  event.preventDefault()
  fetch('https://localhost:8080/api/v1/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify({
      username: event.target.username.value,
      password: event.target.password.value
    })
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        router.push('/totp')
      } else {
        alert('Login failed!')
      }
    })
    .catch((error) => {
      alert('Login failed: ' + error)
      console.log(error)
    })
  event.target.password.value = ''
}
</script>

<template>
  <form id="login-view" @submit="submitLogin" class="padded gapped centered column">
    <h1>Login to RedPepper</h1>
    <label for="username">Username</label>
    <input type="text" id="username" name="username" required placeholder="Username" />
    <label for="password">Password</label>
    <input type="password" id="password" name="password" required placeholder="Password" />
    <button type="submit">Login</button>
  </form>
</template>
