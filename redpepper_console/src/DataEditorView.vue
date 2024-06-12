<script setup>
import { ref, onMounted } from 'vue'
import TreeComponent from './tree/TreeComponent.vue'
import { useRouter } from 'vue-router'
import Fetch from './fetcher'
import { Prompt, Confirm } from './dialogs'
import { useToast } from './toast'

import ace from 'ace-builds'
ace.config.set('basePath', '/assets/ace_modules')
import ace_languages from './languages'
import { lightThemes, darkThemes } from './themes'

const editor = ref(null)
const treeData = ref([])
const selectedPath = ref([])
const currentFile = ref('')
const isChanged = ref(true)
const selectedLanguage = ref('plain_text')
const selectedTheme = ref(localStorage.getItem('aceEditorTheme') || 'chrome')

const router = useRouter()
const toast = useToast()

onMounted(() => {
  refreshTree()
  editor.value = ace.edit('data-editor', {
    theme: 'ace/theme/' + selectedTheme.value,
    mode: 'ace/mode/' + selectedLanguage.value,
    readOnly: true
  })
  editor.value.on('input', () => {
    isChanged.value = !editor.value.session.getUndoManager().isClean()
  })
  editor.value.session.setValue('Select a file to edit its content.')
})

function treeItemSelected(element, path, isParent) {
  selectedPath.value = path
  if (!isParent) {
    openFile(path)
  }
}

function refreshTree() {
  const busy = toast.new('Refreshing file tree...', 'success')
  Fetch('/api/v1/config/tree')
    .onStatus(401, () => {
      busy.close()
      toast.new('Please log in.', 'error')
      router.push('/login')
    })
    .onError((error) => {
      busy.close()
      toast.new('Failed to fetch file tree: ' + error, 'error')
    })
    .onSuccess((data) => {
      busy.close()
      treeData.value = data.tree
    })
    .credentials('same-origin')
    .get()
}

function openFile(path) {
  if (!path || path.length === 0) {
    return
  }
  const busy = toast.new('Opening file...', 'info')
  Fetch('/api/v1/config/file')
    .query('path', path.join('/'))
    .onStatus(401, () => {
      busy.close()
      toast.new('Please log in.', 'error')
      router.push('/login')
    })
    .onError((error) => {
      busy.close()
      toast.new('Failed to open file: ' + error, 'error')
    })
    .onSuccess((data) => {
      busy.close()
      if (!data.success) {
        throw new Error(data.detail)
      }
      let thislang = ''
      const filename = path[path.length - 1].toLowerCase()
      for (let lang of ace_languages) {
        if (lang.filenames && lang.filenames.includes(filename)) {
          thislang = lang.id
          break
        }
      }
      if (thislang == '') {
        const ext = filename.split('.').pop()
        for (let lang of ace_languages) {
          if (lang.ext && lang.ext.includes(ext)) {
            thislang = lang.id
            break
          }
        }
      }
      if (thislang == '') {
        thislang = 'plain_text'
      }
      selectedLanguage.value = thislang
      changeLanguage()
      editor.value.session.setValue(data.content)
      editor.value.setReadOnly(false)
      currentFile.value = path.join('/')
    })
    .credentials('same-origin')
    .get()
}

function changeLanguage() {
  const language = selectedLanguage.value
  editor.value.session.setMode('ace/mode/' + language)
}

function changeTheme() {
  const theme = selectedTheme.value
  editor.value.setTheme('ace/theme/' + theme)
  localStorage.setItem('aceEditorTheme', theme)
}

function saveFile() {
  if (currentFile.value === '') {
    return
  }
  const content = editor.value.getValue()
  const busy = toast.new('Saving file...', 'info')
  Fetch('/api/v1/config/file')
    .query('path', currentFile.value)
    .onStatus(401, () => {
      busy.close()
      toast.new('Please log in.', 'error')
      router.push('/login')
    })
    .onError((error) => {
      busy.close()
      toast.new('Failed to save file: ' + error, 'error')
    })
    .onSuccess((data) => {
      busy.close()
      if (data.success) {
        toast.new('File saved successfully: ' + currentFile.value, 'success')
        editor.value.session.getUndoManager().markClean()
        isChanged.value = false
      } else {
        throw new Error(data.detail)
      }
    })
    .credentials('same-origin')
    .post({ data: content })
}

function newFile() {
  Prompt('Enter the name of the new file')
    .title('New file')
    .initialValue(selectedPath.value.join('/') + '/')
    .onSubmit((filename) => {
      const busy = toast.new('Creating file...', 'info')
      Fetch('/api/v1/config/file')
        .query('path', filename)
        .query('isdir', false)
        .onStatus(401, () => {
          busy.close()
          toast.new('Please log in.', 'error')
          router.push('/login')
        })
        .onError((error) => {
          busy.close()
          toast.new('Failed to create file: ' + error, 'error')
        })
        .onSuccess((data) => {
          busy.close()
          if (data.success) {
            refreshTree()
            toast.new('File created successfully: ' + filename, 'success')
          } else {
            throw new Error(data.detail)
          }
        })
        .credentials('same-origin')
        .put()
    })
    .showModal()
}

function newFolder() {
  Prompt('Enter the name of the new folder')
    .title('New folder')
    .initialValue(selectedPath.value.join('/') + '/')
    .onSubmit((foldername) => {
      const busy = toast.new('Creating folder...', 'info')
      Fetch('/api/v1/config/file')
        .query('path', foldername)
        .query('isdir', true)
        .onStatus(401, () => {
          busy.close()
          toast.new('Please log in.', 'error')
          router.push('/login')
        })
        .onError((error) => {
          busy.close()
          toast.new('Failed to create folder: ' + error, 'error')
        })
        .onSuccess((data) => {
          busy.close()
          if (data.success) {
            refreshTree()
            toast.new('Folder created successfully: ' + foldername, 'success')
          } else {
            throw new Error(data.detail)
          }
        })
        .credentials('same-origin')
        .put()
    })
    .showModal()
}

function deleteFileOrFolder() {
  if (selectedPath.value.length === 0) {
    return
  }
  Confirm('Are you sure you want to delete ' + selectedPath.value.join('/') + '?')
    .onConfirm(() => {
      const busy = toast.new('Deleting file or folder...', 'info')
      Fetch('/api/v1/config/file')
        .query('path', selectedPath.value.join('/'))
        .onStatus(401, () => {
          busy.close()
          toast.new('Please log in.', 'error')
          router.push('/login')
        })
        .onError((error) => {
          busy.close()
          toast.new('Failed to delete file or folder: ' + error, 'error')
        })
        .onSuccess((data) => {
          busy.close()
          if (data.success) {
            refreshTree()
            toast.new(
              'File or folder deleted successfully: ' + selectedPath.value.join('/'),
              'success'
            )
            if (selectedPath.value.join('/') === currentFile.value) {
              editor.value.session.setValue('Select a file to edit its content.')
              editor.value.setReadOnly(true)
              currentFile.value = ''
              selectedPath.value = []
            }
          } else {
            throw new Error(data.detail)
          }
        })
        .credentials('same-origin')
        .delete()
    })
    .showModal()
}

function renameFileOrFolder() {
  if (selectedPath.value.length === 0) {
    return
  }
  const oldPath = selectedPath.value.join('/')
  Prompt('Enter the new name for ' + oldPath)
    .title('Rename file or folder')
    .initialValue(oldPath)
    .onSubmit((newPath) => {
      const busy = toast.new('Renaming file or folder...', 'info')
      Fetch('/api/v1/config/file')
        .query('path', oldPath)
        .onStatus(401, () => {
          busy.close()
          toast.new('Please log in.', 'error')
          router.push('/login')
        })
        .onError((error) => {
          busy.close()
          toast.new('Failed to rename file or folder: ' + error, 'error')
        })
        .onSuccess((data) => {
          busy.close()
          if (data.success) {
            refreshTree()
            toast.new(
              'File or folder renamed successfully: ' + oldPath + ' -> ' + newPath,
              'success'
            )
            if (oldPath === currentFile.value) {
              currentFile.value = newPath
              selectedPath.value = []
            }
          } else {
            throw new Error(data.detail)
          }
        })
        .credentials('same-origin')
        .patch({ path: newPath })
    })
    .showModal()
}
</script>

<template>
  <div id="data-editor-view" class="full-height column">
    <h1>Data Editor</h1>
    <div>
      <div class="gapped centered row">
        <button @click="refreshTree">Refresh</button>
        <button @click="newFile">+File</button>
        <button @click="newFolder">+Folder</button>
        <button
          @click="deleteFileOrFolder"
          v-show="selectedPath.length"
          style="color: var(--color-red)"
        >
          Delete
        </button>
        <button @click="renameFileOrFolder" v-show="selectedPath.length">Rename</button>
        <button
          @click="saveFile"
          v-show="isChanged && currentFile !== ''"
          style="color: var(--color-green)"
        >
          Save
        </button>
        <span v-show="currentFile !== '' && !isChanged">&#10004; No changes</span>
      </div>
    </div>
    <div class="full-height full-width row">
      <TreeComponent id="file-tree" :model="treeData" @item-selected="treeItemSelected" class="" />
      <div class="full-height column" id="data-editor-container">
        <span class="text-centered">{{ currentFile }}</span>
        <div id="data-editor" class="full-height bordered rounded large-font"></div>
        <div class="gapped centered justify-centered thinly-padded row">
          <span class="hide-on-text-overflow">Language:</span>
          <select v-model="selectedLanguage" @change="changeLanguage">
            <option v-for="lang in ace_languages" :value="lang.id" :key="lang.id">
              {{ lang.name }}
            </option>
          </select>
          <span class="hide-on-text-overflow">Theme:</span>
          <select v-model="selectedTheme" @change="changeTheme">
            <option disabled>--- Light ---</option>
            <option v-for="theme in lightThemes" :value="theme.id" :key="theme.id">
              {{ theme.name }}
            </option>
            <option disabled>--- Dark ---</option>
            <option v-for="theme in darkThemes" :value="theme.id" :key="theme.id">
              {{ theme.name }}
            </option>
          </select>
          <span class="hide-on-text-overflow small-font"
            >Powered by <a href="https://ace.c9.io/" target="_blank">Ace Editor</a></span
          >
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
#file-tree {
  margin: 0.5rem 0;
  width: 25%;
}
#data-editor-container {
  margin: 0.5rem;
  width: 75%;
}
</style>
