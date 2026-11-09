const moeda = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const numero = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 })
const vazio = (valor) => valor === null || valor === undefined

export const formatarMoeda = (valor) => moeda.format(Number(valor || 0))
export const formatarNumero = (valor) => (vazio(valor) ? '—' : numero.format(valor))
export const formatarData = (iso) => (iso ? iso.split('-').reverse().join('/') : '—')
export const comSinal = (valor, formatar = formatarNumero) => `${valor > 0 ? '+' : ''}${formatar(valor)}`
export const formatarPercentual = (valor) => `${comSinal(valor)}%`
export const rotuloProduto = (produto) => `${produto.fabrica} · Código ${produto.sku}`

export function formatarValor(valor, formato) {
  if (vazio(valor)) return formato === 'percentual' ? 'Sem base' : '—'
  if (formato === 'moeda') return formatarMoeda(valor)
  if (formato === 'data') return formatarData(valor)
  if (formato === 'percentual') return formatarPercentual(valor)
  if (formato === 'numero') return formatarNumero(valor)
  return valor
}

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

export function formatarDataHora(valor) {
  if (!valor) return '—'
  const iso = /Z$|[+-]\d\d:\d\d$/.test(valor) ? valor : `${valor}Z`
  const data = new Date(iso)
  return Number.isNaN(data.getTime()) ? '—' : data.toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo', dateStyle: 'short', timeStyle: 'short' })
}
