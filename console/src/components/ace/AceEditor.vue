<script setup lang="ts">
import { edit, Ace } from 'ace-builds'
import ResizeObserver from 'resize-observer-polyfill'

const content = defineModel<string>({ required: true })
const editor = ref<Ace.Editor>()
const saved = defineModel<boolean>('saved', { default: false })
const editordiv = ref<HTMLDivElement>()
const ro = ref<ResizeObserver>()
const setting_content = ref<boolean>(false)
const content_copy = ref<string>()

const props = withDefaults(
  defineProps<{
    theme: string
    mode: string
    readonly: boolean
  }>(),
  {
    theme: 'ace/theme/monokai',
    mode: 'ace/mode/plain_text',
    readonly: false
  }
)

const setSaved = () => {
  try {
    setting_content.value = true
    editor.value!.session.getUndoManager().markClean()
  } finally {
    setting_content.value = false
  }
  saved.value = true
}

defineExpose({
  setSaved
})

onMounted(() => {
  editor.value = edit(editordiv.value!)
  editor.value.on('change', () => {
    if (!setting_content.value) {
      content.value = content_copy.value = editor.value!.getValue()
      saved.value = editor.value!.session.getUndoManager().isClean()
    }
  })
  ro.value = new ResizeObserver(() => {
    editor.value?.resize()
  })
  ro.value.observe(editordiv.value!)
})

onBeforeUnmount(() => {
  ro.value?.disconnect()
  editor.value?.destroy()
})

watchEffect(() => {
  if (!editor.value) return
  if (setting_content.value) return
  if (content.value === content_copy.value) return
  try {
    setting_content.value = true
    editor.value.session.setValue(content.value)
    content_copy.value = content.value
  } finally {
    setting_content.value = false
  }
})

watchEffect(() => {
  if (!editor.value) return
  editor.value.setTheme('ace/theme/' + props.theme)
})

watchEffect(() => {
  if (!editor.value) return
  editor.value.session.setMode('ace/mode/' + props.mode)
})

watchEffect(() => {
  if (!editor.value) return
  editor.value.setReadOnly(props.readonly)
})
</script>
<template>
  <div ref="editordiv" />
</template>
