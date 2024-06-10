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
    if (this.toasts.length >= this.options.maxToasts) {
      this.toasts[0].close()
    }
    options = {
      ...this.options,
      ...options,
      controller: this,
      type,
      message
    }
    const toast = new Toast(options)
    this.toasts.push(toast)
    toast.show()
    this.reposition()
    return toast
  }

  _remove(toast) {
    const index = this.toasts.indexOf(toast)
    if (index >= 0) {
      this.toasts.splice(index, 1)
      this.reposition()
    }
  }

  reposition() {
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
    this.toast = document.createElement('div')
    this.toast.style.position = 'absolute'
    this.toast.style.bottom = '1rem'
    this.toast.style.left = '50vw'
    this.toast.style.zIndex = '10000'
    this.toast.style.borderRadius = '1em'
    this.toast.style.transform = 'translateX(-50%)'
    this.toast.classList.add('toast')
    if (options.type) {
      this.toast.classList.add(`toast-${options.type}`)
    }
    this.text = document.createElement('span')
    this.text.innerText = options.message
    this.text.classList.add('toast-text')
    this.toast.appendChild(this.text)
    this.closeBtn = document.createElement('button')
    this.closeBtn.type = 'button'
    this.closeBtn.innerText = '\u00D7'
    this.closeBtn.classList.add('toast-close')
    this.closeBtn.onclick = () => {
      this.close()
    }
    this.toast.appendChild(this.closeBtn)
  }

  show() {
    document.body.appendChild(this.toast)
    if (this.options.timeout > 0) {
      setTimeout(() => {
        this.close()
      }, this.options.timeout)
    }
  }

  close() {
    this.options.controller._remove(this)
    this.toast.remove()
  }
}

function useToast() {
  const controller = inject('toast')
  return controller
}

export default {
  install: (app, options) => {
    const controller = new ToastController(options)
    app.provide('toast', controller)
    app.config.globalProperties.$toast = controller
  }
}
export { useToast }
