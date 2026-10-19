export function dataLocal(data = new Date()) {
  return [data.getFullYear(), String(data.getMonth() + 1).padStart(2, '0'), String(data.getDate()).padStart(2, '0')].join('-')
}
export function diasAtras(dias) {
  const data = new Date()
  data.setDate(data.getDate() - dias)
  return dataLocal(data)
}
export function formatarData(valor) { return valor ? valor.split('-').reverse().join('/') : '—' }
export function formatarDataHora(valor) {
  if (!valor) return '—'
  const iso = /Z$|[+-]\d\d:\d\d$/.test(valor) ? valor : `${valor}Z`
  const data = new Date(iso)
  return Number.isNaN(data.getTime()) ? '—' : data.toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo', dateStyle: 'short', timeStyle: 'short' })
}
