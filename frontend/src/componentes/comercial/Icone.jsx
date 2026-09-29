const desenhos = {
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
  local: 'M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0ZM15 10a3 3 0 1 1-6 0 3 3 0 0 1 6 0',
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
