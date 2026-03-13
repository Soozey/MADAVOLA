import { describe, expect, it } from 'vitest'
import { buildRoleOptionsByFilieres } from '../rbacOptions'

describe('buildRoleOptionsByFilieres', () => {
  it('shows BOIS roles and common roles when filiere=BOIS', () => {
    const rows = [
      { code: 'orpailleur', label: 'Orpailleur', filiere_scope: ['OR'] },
      { code: 'bois_exploitant', label: 'Bois Exploitant', filiere_scope: ['BOIS'] },
      { code: 'admin', label: 'Admin', filiere_scope: ['OR', 'PIERRE', 'BOIS'] },
    ]
    const options = buildRoleOptionsByFilieres(['BOIS'], rows)
    expect(options.map((o) => o.value)).toContain('bois_exploitant')
    expect(options.map((o) => o.value)).toContain('admin')
    expect(options.map((o) => o.value)).not.toContain('orpailleur')
  })

  it('keeps merged unique roles for multi-filiere selection', () => {
    const rows = [
      { code: 'pierre_collecteur', label: 'Pierre Collecteur', filiere_scope: ['PIERRE'] },
      { code: 'bois_collecteur', label: 'Bois Collecteur', filiere_scope: ['BOIS'] },
      { code: 'admin', label: 'Admin', filiere_scope: ['OR', 'PIERRE', 'BOIS'] },
      { code: 'admin', label: 'Admin', filiere_scope: ['OR', 'PIERRE', 'BOIS'] },
    ]
    const options = buildRoleOptionsByFilieres(['PIERRE', 'BOIS'], rows)
    const codes = options.map((o) => o.value)
    expect(codes).toContain('pierre_collecteur')
    expect(codes).toContain('bois_collecteur')
    expect(codes.filter((c) => c === 'admin').length).toBe(1)
  })
})
