const tons = {
  Alta: 'atencao',
  Média: 'aviso',
  Baixa: 'neutro',
  Ativo: 'verde',
  Atenção: 'aviso',
  Inativo: 'neutro',
  'Inativo na Fábrica': 'atencao',
  'Ciclo Atrasado': 'aviso',
  'Reposição Atrasada': 'aviso',
  'Janela Ideal': 'verde',
  'Janela de Recompra (7 dias)': 'verde',
}

export default function Etiqueta({ texto }) {
  return <span className={`etiqueta etiqueta-${tons[texto] || 'neutro'}`}>{texto}</span>
}
