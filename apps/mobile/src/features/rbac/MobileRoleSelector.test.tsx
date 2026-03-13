import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { MobileRoleSelector } from './MobileRoleSelector'
import type { RbacRole } from './types'

const roles: RbacRole[] = [
  { code: 'wood_transporter', label: 'Transporteur', category: 'Transport', actor_type: 'USAGER' },
  { code: 'wood_admin', label: 'Admin bois', category: 'Administration', actor_type: 'AGENT_ETAT' },
]

describe('MobileRoleSelector', () => {
  it('filters roles and selects one', async () => {
    const user = userEvent.setup()
    const onRoleSelect = vi.fn()

    render(
      <MobileRoleSelector
        filiere="BOIS"
        onFiliereChange={() => {}}
        selectedRole=""
        onRoleSelect={onRoleSelect}
        roles={roles}
        search=""
        onSearchChange={() => {}}
        category="Transport"
        onCategoryChange={() => {}}
        actorType="USAGER"
        onActorTypeChange={() => {}}
      />,
    )

    expect(screen.getByText('Transporteur')).toBeInTheDocument()
    expect(screen.queryByText('Admin bois')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /Transporteur/i }))
    expect(onRoleSelect).toHaveBeenCalledWith('wood_transporter')
  })
})
