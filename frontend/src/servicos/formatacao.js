const moeda = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const numero = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 })

export const formatarMoeda = (valor) => moeda.format(Number(valor || 0))
export const formatarNumero = (valor) => numero.format(valor)
export const formatarData = (iso) => (iso ? iso.split('-').reverse().join('/') : '—')

export function dataLocal(data = new Date()) {
  const mes = String(data.getMonth() + 1).padStart(2, '0')
  const dia = String(data.getDate()).padStart(2, '0')
  return `${data.getFullYear()}-${mes}-${dia}`
}
export function diasAtras(dias) {
  const data = new Date()
  data.setDate(data.getDate() - dias)
  return dataLocal(data)
}
