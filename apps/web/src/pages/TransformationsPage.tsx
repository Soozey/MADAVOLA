import { useMutation } from '@tanstack/react-query'
import { api } from '../lib/api'

export default function TransformationsPage() {
  const mutation = useMutation({
    mutationFn: async (payload: any) => api.createTransformation(payload),
  })

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    const inputIds = String(fd.get('input_lot_ids') || '')
      .split(',')
      .map((x) => Number(x.trim()))
      .filter((x) => Number.isFinite(x) && x > 0)
    const outputs = String(fd.get('outputs') || '')
      .split(',')
      .map((token) => token.trim())
      .filter(Boolean)
      .map((token) => {
        const [quantity, unit, wood_form] = token.split(':')
        return { quantity: Number(quantity), unit: unit || 'm3', wood_form: wood_form || 'planche' }
      })
    mutation.mutate({
      operation_type: String(fd.get('operation_type') || 'sciage'),
      input_lot_ids: inputIds,
      outputs,
      notes: String(fd.get('notes') || ''),
    })
  }

  return (
    <div className="lots-page">
      <div className="page-header"><h1>Transformations BOIS</h1></div>
      <div className="card form-card">
        <h2>Input lots to output lots</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <div className="form-group"><label>Operation *</label><input name="operation_type" defaultValue="sciage" required /></div>
            <div className="form-group"><label>Input lot IDs *</label><input name="input_lot_ids" placeholder="12,13" required /></div>
            <div className="form-group"><label>Outputs *</label><input name="outputs" placeholder="2.5:m3:planche,1.0:m3:lot_scie" required /></div>
            <div className="form-group"><label>Notes</label><input name="notes" /></div>
          </div>
          <div className="form-actions"><button className="btn-primary" type="submit">Executer</button></div>
        </form>
        {mutation.data && <pre>{JSON.stringify(mutation.data, null, 2)}</pre>}
      </div>
    </div>
  )
}
