export type FiliereCode = 'OR' | 'PIERRE' | 'BOIS'

export interface RbacRole {
  code: string
  label?: string
  description?: string
  category?: string
  actor_type?: 'USAGER' | 'AGENT_ETAT' | 'OPERATEUR_PRIVE' | 'TRANSVERSAL'
}
