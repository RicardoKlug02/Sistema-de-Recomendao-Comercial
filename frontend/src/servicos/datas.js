export function dataLocal(data = new Date()) {
  return [data.getFullYear(), String(data.getMonth() + 1).padStart(2, '0'), String(data.getDate()).padStart(2, '0')].join('-')
}
export function diasAtras(dias) {
  const data = new Date()
  data.setDate(data.getDate() - dias)
  return dataLocal(data)
}
export function formatarData(valor) { return valor ? valor.split('-').reverse().join('/') : '—' }