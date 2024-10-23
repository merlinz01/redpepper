import { defineStore } from 'pinia'

export interface Message {
  text: string
  timeout?: number
  type?: 'success' | 'error' | 'warning' | 'info'
  id?: string
}

const useMessages = defineStore('notifications', () => {
  const messages = ref<Message[]>([])
  const currentMessage = computed(() => {
    if (messages.value.length === 0) return null
    return messages.value[messages.value.length - 1]
  })
  function addMessage(message: Message): string {
    if (!message.id) {
      message.id = Math.random().toString(36)
    } else {
      removeMessage(message.id)
    }
    if (message.timeout === undefined) message.timeout = 5000
    messages.value.push(message)
    if (message.timeout !== 0) {
      setTimeout(() => {
        removeMessage(message.id!)
      }, message.timeout)
    }
    return message.id
  }
  function removeMessage(messageId: string) {
    messages.value = messages.value.filter((m) => m.id !== messageId)
  }
  return {
    messages,
    currentMessage,
    addMessage,
    removeMessage
  }
})

export default useMessages
