import { inject } from 'vue'

class ToastController {
  constructor(options) {
    this.options = options || {}
    this.options.spacing = this.options.spacing || 4
    this.options.maxToasts = this.options.maxToasts || 5
    this.options.timeout = this.options.timeout || 10000
    this.toasts = []
  }

  new(message, type, options) {
    // Close any toast with the same options.id
    if (options && options.id) {
      for (const toast of this.toasts) {
        if (toast.options.id === options.id) {
          toast.close()
        }
      }
    }
    // Remove the oldest toast if we have reached the max
    if (this.toasts.length >= this.options.maxToasts) {
      this.toasts[0].close()
    }
    // Build the toast options
    options = {
      ...this.options,
      ...options,
      controller: this,
      type,
      message
    }
    // Create the toast object
    const toast = new Toast(options)
    // Add it to the list
    this.toasts.push(toast)
    // Show the toast
    toast.show()
    // Reposition the toast stack
    this.reposition()
    return toast
  }

  _remove(toast) {
    // Remove the toast from the list
    const index = this.toasts.indexOf(toast)
    if (index >= 0) {
      this.toasts.splice(index, 1)
      this.reposition()
    }
  }

  reposition() {
    // Position the toasts from the bottom up
    let bottom = 1
    for (const toast of this.toasts) {
      toast.toast.style.bottom = `${bottom}rem`
      bottom += this.options.spacing
    }
  }
}
class Toast {
  constructor(options) {
    this.options = options
    // <div class="toast toast-info">
    this.toast = document.createElement('div')
    this.toast.style.position = 'absolute'
    this.toast.style.bottom = '1rem'
    this.toast.style.right = '1rem'
    this.toast.style.zIndex = '10000'
    this.toast.style.borderRadius = '1em'
    this.toast.classList.add('toast')
    if (options.type) {
      this.toast.classList.add(`toast-${options.type}`)
    }
    // <span class="toast-text">Hello, Toasts!</span>
    this.text = document.createElement('span')
    this.text.innerText = options.message
    this.text.classList.add('toast-text')
    this.toast.appendChild(this.text)
    // <button type="button" class="toast-close">&times;</button>
    this.closeBtn = document.createElement('button')
    this.closeBtn.type = 'button'
    this.closeBtn.innerText = '\xD7'
    this.closeBtn.classList.add('toast-close')
    this.closeBtn.onclick = () => {
      this.close()
    }
    this.toast.appendChild(this.closeBtn)
    // </div>
  }

  show() {
    // Add the toast to the body
    document.body.appendChild(this.toast)
    // Auto-close the toast after options.timeout milliseconds
    if (this.options.timeout > 0) {
      setTimeout(() => {
        this.close()
      }, this.options.timeout)
    }
  }

  close() {
    // Remove the toast from the controller list
    this.options.controller._remove(this)
    // Remove the toast from the body
    this.toast.remove()
  }
}

// Function for use by Vue composition-style components
function useToast() {
  const controller = inject('toast')
  return controller
}

export default {
  install: (app, options) => {
    // Create a new controller
    const controller = new ToastController(options)
    // Provide the controller to the app for useToast()
    app.provide('toast', controller)
    // Also provide the controller as a global property: this.$toast
    app.config.globalProperties.$toast = controller
  }
}
export { useToast }
