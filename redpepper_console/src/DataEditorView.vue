<script setup>
import { ref, onMounted } from 'vue'
import TreeComponent from './tree/TreeComponent.vue'

import ace from 'ace-builds'
ace.config.set('basePath', 'node_modules/ace-builds/src-noconflict')
import ace_languages from './languages'

onMounted(() => {
  refreshTree()
  editor.value = ace.edit('data-editor', {
    theme: 'ace/theme/' + selectedTheme.value,
    mode: 'ace/mode/' + selectedLanguage.value
  })
})

const editor = ref(null)
const treeData = ref([])
const selectedPath = ref([])
const isChanged = ref(true)
const selectedLanguage = ref('plain_text')
const selectedTheme = ref('chrome')

function treeItemSelected(element, path, isParent) {
  if (!isParent) {
    selectedPath.value = path
    openFile(path)
  }
}

function refreshTree() {
  fetch('https://localhost:8080/api/v1/config/tree', {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    }
  })
    .then((response) => response.json())
    .then((data) => {
      treeData.value = data.tree
    })
    .catch((error) => {
      alert('Error retrieving file tree: ', error)
    })
}

function getFileContent(path) {
  return fetch('https://localhost:8080/api/v1/config/file?path=' + path.join('/'), {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    }
  })
    .then((response) => response.json())
    .then((data) => {
      return { success: true, content: data.data }
    })
    .catch((error) => {
      alert('Error retrieving file content: ', error)
      return { success: false, content: '' }
    })
}
async function openFile(path) {
  if (!path || path.length === 0) {
    return
  }
  const content = await getFileContent(path)
  if (!content.success) {
    return
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
  editor.value.setValue(content.content)
  editor.value.clearSelection()
  editor.value.gotoLine(0)
}

function changeLanguage() {
  const language = selectedLanguage.value
  editor.value.session.setMode('ace/mode/' + language)
}

function changeTheme() {
  const theme = selectedTheme.value
  editor.value.setTheme('ace/theme/' + theme)
}

function saveFile() {
  if (selectedPath.value.length === 0) {
    return
  }
  const content = editor.value.getValue()
  fetch('https://localhost:8080/api/v1/config/file?path=' + selectedPath.value.join('/'), {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ data: content })
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        alert('File saved successfully')
      } else {
        alert('Error saving file: ', data.detail)
      }
    })
    .catch((error) => {
      alert('Error saving file: ', error)
    })
}
</script>

<template>
  <div id="data-editor-view" class="full-height no-shrink padded column">
    <h1>Data Editor</h1>
    <div>
      <div class="gapped centered row">
        <button @click="refreshTree">Refresh</button>
        <button @click="newFile">New File</button>
        <button @click="newFolder">New Folder</button>
        <button @click="saveFile" v-show="isChanged">Save</button>
        Language:
        <select v-model="selectedLanguage" @change="changeLanguage">
          <option v-for="lang in ace_languages" :value="lang.id" :key="lang.id">
            {{ lang.name }}
          </option>
        </select>
        Theme:
        <select v-model="selectedTheme" @change="changeTheme">
          <option disabled>--- Light ---</option>
          <option value="chrome">Chrome</option>
          <option value="cloud_editor">CloudEditor</option>
          <option value="clouds">Clouds</option>
          <option value="cloud9_day">Cloud9 Day</option>
          <option value="crimson_editor">Crimson Editor</option>
          <option value="dawn">Dawn</option>
          <option value="dreamweaver">Dreamweaver</option>
          <option value="eclipse">Eclipse</option>
          <option value="github">GitHub</option>
          <option value="gruvbox_light_hard">Gruvbox Light Hard</option>
          <option value="iplastic">IPlastic</option>
          <option value="katzenmilch">KatzenMilch</option>
          <option value="kuroir">Kuroir</option>
          <option value="solarized_light">Solarized Light</option>
          <option value="sqlserver">SQL Server</option>
          <option value="textmate">TextMate</option>
          <option value="tomorrow">Tomorrow</option>
          <option value="xcode">XCode</option>
          <option disabled>--- Dark ---</option>
          <option value="ambiance">Ambiance</option>
          <option value="chaos">Chaos</option>
          <option value="cloud_editor_dark">CloudEditor Dark</option>
          <option value="clouds_midnight">Clouds Midnight</option>
          <option value="cloud9_night">Cloud9 Night</option>
          <option value="cloud9_night_low_color">Cloud9 Night Low Color</option>
          <option value="cobalt">Cobalt</option>
          <option value="dracula">Dracula</option>
          <option value="github_dark">GitHub Dark</option>
          <option value="gob">Green on Black</option>
          <option value="gruvbox">Gruvbox</option>
          <option value="gruvbox_dark_hard">Gruvbox Dark Hard</option>
          <option value="idle_fingers">Idle Fingers</option>
          <option value="kr_theme">krTheme</option>
          <option value="merbivore">Merbivore</option>
          <option value="merbivore_soft">Merbivore Soft</option>
          <option value="mono_industrial">Mono Industrial</option>
          <option value="monokai">Monokai</option>
          <option value="nord_dark">Nord Dark</option>
          <option value="one_dark">One Dark</option>
          <option value="pastel_on_dark">Pastel on Dark</option>
          <option value="solarized_dark">Solarized Dark</option>
          <option value="terminal">Terminal</option>
          <option value="tomorrow_night">Tomorrow Night</option>
          <option value="tomorrow_night_blue">Tomorrow Night Blue</option>
          <option value="tomorrow_night_bright">Tomorrow Night Bright</option>
          <option value="tomorrow_night_eighties">Tomorrow Night 80s</option>
          <option value="twilight">Twilight</option>
          <option value="vibrant_ink">Vibrant Ink</option>
        </select>
      </div>
    </div>
    <div class="full-height full-width row">
      <TreeComponent
        id="file-tree"
        :model="treeData"
        @item-selected="treeItemSelected"
        class="full-height"
      />
      <div class="full-height column" id="data-editor-container">
        <span>{{ '/' + selectedPath.join('/') }}</span>
        <div id="data-editor"></div>
        <span style="text-align: right; font-size: small"
          >Powered by <a href="https://ace.c9.io/" target="_blank">Ace Editor</a></span
        >
      </div>
    </div>
  </div>
</template>

<style scoped>
#file-tree {
  margin: 0.5rem 0;
  width: 25%;
  border-radius: var(--border-radius);
  background-color: var(--color-background-input);
}
#data-editor-container {
  margin: 0.5rem;
  width: 75%;
}
#data-editor {
  height: 100%;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  background-color: var(--color-background-input);
  font-size: large;
}
</style>
