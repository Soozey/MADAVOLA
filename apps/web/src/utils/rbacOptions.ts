export type RbacRoleRow = {
  code: string
  label?: string
  filiere_scope?: string[]
}

const ALL_FILIERES = new Set(['OR', 'PIERRE', 'BOIS'])

function isCommonScope(scope: string[]): boolean {
  if (scope.length !== 3) return false
  return scope.every((f) => ALL_FILIERES.has(f))
}

export function buildRoleOptionsByFilieres(
  selectedFilieres: string[],
  roleRows: RbacRoleRow[]
): Array<{ value: string; label: string }> {
  const selected = new Set(selectedFilieres.map((f) => f.toUpperCase()))
  const byCode = new Map<string, { value: string; label: string; scope: string[] }>()

  for (const row of roleRows) {
    const scope = (row.filiere_scope ?? ['OR', 'PIERRE', 'BOIS']).map((s) => s.toUpperCase())
    const hasMatch = scope.some((f) => selected.has(f)) || isCommonScope(scope)
    if (!hasMatch) continue
    if (!byCode.has(row.code)) {
      byCode.set(row.code, {
        value: row.code,
        label: row.label || row.code,
        scope,
      })
    }
  }

  return Array.from(byCode.values())
    .sort((a, b) => {
      const aScoped = a.scope.length === 1 && selected.has(a.scope[0])
      const bScoped = b.scope.length === 1 && selected.has(b.scope[0])
      if (aScoped && !bScoped) return -1
      if (!aScoped && bScoped) return 1
      return a.value.localeCompare(b.value)
    })
    .map((r) => ({ value: r.value, label: r.label }))
}
