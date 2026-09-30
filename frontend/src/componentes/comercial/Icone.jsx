const desenhos = {
  alertas: 'M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4',
  usuarios: 'M12 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8M5 21v-3a7 7 0 0 1 14 0v3',
  vendas: 'M3 7h18v14H3zM8 7V5a4 4 0 0 1 8 0v2M8 11h8',
  grafico: 'M3 3v18h18M7 14l4-4 4 2 5-7',
  atualizar: 'M20 7v5h-5M4 17v-5h5M6 6a8 8 0 0 1 14 6M4 12a8 8 0 0 0 14 6',

  painel: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
  clientes:
    'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8 M22 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75',
  importacoes: 'M12 16V3m-5 5 5-5 5 5M4 15v6h16v-6',
  busca: 'M21 21l-5-5 M18 10.5a7.5 7.5 0 1 0-15 0 7.5 7.5 0 0 0 15 0',
  seta: 'M5 12h14m-5-5 5 5-5 5',
  sair: 'M9 4H4v16h5m5-13 5 5-5 5M8 12h11',
  oportunidade: 'm13 2-9 12h7l-1 8 10-12h-7z',
  calendario: 'M4 5h16v16H4zM8 3v4m8-4v4M4 10h16',
  fechar: 'm6 6 12 12M6 18 18 6',
  local:
    'M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0ZM15 10a3 3 0 1 1-6 0 3 3 0 0 1 6 0',
}

// Mantém os ícones decorativos consistentes sem dependências adicionais.
export default function Icone({ nome, tamanho = 20 }) {
  return (
    <svg
      width={tamanho}
      height={tamanho}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={desenhos[nome] || desenhos.oportunidade} />
    </svg>
  )
}
