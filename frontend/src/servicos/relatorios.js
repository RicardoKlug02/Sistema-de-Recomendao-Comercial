export const tiposRelatorio = {
  rede: 'Códigos comprados pela rede',
  mapa: 'Mapa cliente x fábrica',
  reativacoes: 'Resultado das reativações',
  inativos: 'Clientes inativos',
  precos: 'Evolução dos preços por código',
  regioes: 'Regiões imediatas por vendedor',
}
export const ehRelatorioDePosicao = (tipo) => ['mapa', 'inativos'].includes(tipo)
