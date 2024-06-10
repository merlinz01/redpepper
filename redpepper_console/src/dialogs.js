// Dialog boxes for user interaction.
//
// Usage:
//   import { Alert, Confirm, Prompt } from './dialogs.js'
//   Alert('This is an alert!').show()
//   Confirm('Are you sure?').onConfirm(() => {
//     console.log('Confirmed!')
//   }).onCancel(() => {
//     console.log('Cancelled!')
//   }).showModal()
//   Prompt('Enter your name:').onSubmit((value) => {
//     console.log('Submitted:', value)
//   }).showModal()

// Base class for styleable modal dialog boxes.
// This class is not meant to be used directly, but to be inherited by AlertDialog, ConfirmDialog, and PromptDialog classes.
class Dialog {
  constructor() {
    this.dialog = null
    this._on_close = null
  }

  onClose(callback) {
    this._on_close = callback
    return this
  }

  build() {
    this.dialog = document.createElement('dialog')
    this.dialog.style.cssText = `
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 10000;
        max-width: 90vw;
        min-width: 20vw;
    `
    this.dialog.addEventListener('close', () => {
      if (this._on_close !== null) {
        this._on_close()
      }
      this.dialog.remove()
    })
    document.body.appendChild(this.dialog)
    return this.dialog
  }

  show() {
    this.build()
    this.dialog.show()
  }

  showModal() {
    this.build()
    this.dialog.showModal()
  }
}

// Alert dialog box.
// Note: for non-urgent notifications, a toast-style notification is more user-friendly.
class AlertDialog extends Dialog {
  constructor(message) {
    super()
    this._message = message
    this._title = 'Alert'
  }

  title(title) {
    this._title = title
    return this
  }

  build() {
    super.build()
    this.dialog.appendChild(this.createContent())
    return this.dialog
  }

  createContent() {
    const content = document.createElement('div')
    content.appendChild(this.createTitle())
    content.appendChild(this.createMessage())
    content.appendChild(this.createButton())
    return content
  }

  createTitle() {
    const title = document.createElement('h3')
    title.innerText = this._title
    return title
  }

  createMessage() {
    const message = document.createElement('p')
    message.innerText = this._message
    return message
  }

  createButton() {
    const button = document.createElement('button')
    button.innerText = 'OK'
    button.autofocus = true
    button.addEventListener('click', () => {
      this.dialog.close()
    })
    return button
  }
}

// Confirm dialog box.
class ConfirmDialog extends Dialog {
  constructor(message) {
    super()
    this._message = message
    this._title = 'Confirm'
    this._on_confirm = null
    this._on_cancel = null
  }

  title(title) {
    this._title = title
    return this
  }

  onConfirm(callback) {
    this._on_confirm = callback
    return this
  }

  onCancel(callback) {
    this._on_cancel = callback
    return this
  }

  build() {
    super.build()
    this.dialog.appendChild(this.createContent())
    return this.dialog
  }

  createContent() {
    const form = document.createElement('form')
    form.appendChild(this.createTitle())
    form.appendChild(this.createMessage())
    form.appendChild(this.createButtons())
    return form
  }

  createTitle() {
    const title = document.createElement('h3')
    title.innerText = this._title
    return title
  }

  createMessage() {
    const message = document.createElement('p')
    message.innerText = this._message
    return message
  }

  createButtons() {
    const buttons = document.createElement('div')
    // OK button has to be added first to make it be clicked when pressing Enter
    const ok = document.createElement('button')
    ok.innerText = 'OK'
    ok.style.marginTop = '1em'
    ok.style.marginRight = '1em'
    ok.addEventListener('click', () => {
      if (this._on_confirm !== null) {
        this._on_confirm()
      }
      this.dialog.close()
    })
    buttons.appendChild(ok)
    const cancel = document.createElement('button')
    cancel.innerText = 'Cancel'
    cancel.style.marginTop = '1em'
    cancel.style.marginRight = '1em'
    cancel.addEventListener('click', () => {
      if (this._on_cancel !== null) {
        this._on_cancel()
      }
      this.dialog.close()
    })
    buttons.appendChild(cancel)
    return buttons
  }
}

// Prompt dialog box.
class PromptDialog extends Dialog {
  constructor(prompt) {
    super()
    this._prompt = prompt
    this._input_type = 'text'
    this._title = 'Prompt'
    this._initial_value = undefined
    this._on_submit = null
  }

  title(title) {
    this._title = title
    return this
  }

  inputType(type) {
    this._input_type = type
    return this
  }

  initialValue(value) {
    this._initial_value = value
    return this
  }

  onSubmit(callback) {
    this._on_submit = callback
    return this
  }

  build() {
    super.build()
    this.dialog.appendChild(this.createContent())
    return this.dialog
  }

  createContent() {
    const form = document.createElement('form')
    form.method = 'dialog'
    form.addEventListener('submit', () => {
      if (this._on_submit !== null) {
        this._on_submit(this.input.value)
      }
    })
    form.appendChild(this.createTitle())
    form.appendChild(this.createPrompt())
    form.appendChild(this.createInput())
    form.appendChild(this.createButtons())
    return form
  }

  createTitle() {
    const title = document.createElement('h3')
    title.innerText = this._title
    return title
  }

  createPrompt() {
    const prompt = document.createElement('p')
    prompt.innerText = this._prompt
    return prompt
  }

  createInput() {
    const input = document.createElement('input')
    input.type = this._input_type
    input.style.width = '100%'
    input.autofocus = true
    input.required = true
    if (this._initial_value !== undefined) {
      input.value = this._initial_value
    }
    this.input = input
    return input
  }

  createButtons() {
    const buttons = document.createElement('div')
    // OK button has to be added first to make it be clicked when pressing Enter
    const ok = document.createElement('button')
    ok.innerText = 'OK'
    ok.style.marginTop = '1em'
    ok.style.marginRight = '1em'
    ok.type = 'submit'
    buttons.appendChild(ok)
    const cancel = document.createElement('button')
    cancel.innerText = 'Cancel'
    cancel.style.marginTop = '1em'
    cancel.style.marginRight = '1em'
    cancel.addEventListener('click', (e) => {
      e.preventDefault()
      this.dialog.close()
    })
    buttons.appendChild(cancel)
    return buttons
  }
}

// Create an alert dialog box.
// Note: for non-urgent notifications, a toast-style notification is more user-friendly.
export function Alert(message) {
  return new AlertDialog(message)
}

// Create a confirm dialog box.
export function Confirm(message) {
  return new ConfirmDialog(message)
}

// Create a prompt dialog box.
export function Prompt(prompt) {
  return new PromptDialog(prompt)
}
