export class Selector {
  selected: HTMLElement | null
  onSelect: ((node: HTMLElement, path: string[], isParent: boolean) => void) | null

  constructor() {
    this.selected = null
    this.onSelect = null
  }

  select(node: HTMLElement, path: string[], isParent: boolean) {
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
