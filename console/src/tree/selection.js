export class Selector {
  constructor() {
    this.selected = null
    this.onSelect = null
  }

  select(node, path, isParent) {
    if (this.selected) {
      if (this.selected === node) {
        return false
      }
      this.selected.classList.remove('selected')
    }
    this.selected = node
    this.selected.classList.add('selected')
    if (this.onSelect) {
      this.onSelect(node, path, isParent)
    }
    return true
  }
}
