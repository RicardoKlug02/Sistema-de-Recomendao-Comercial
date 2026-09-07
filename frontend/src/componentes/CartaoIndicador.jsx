import Cartao from './Cartao'

// Apresenta um indicador comercial e seu contexto de comparação.
export default function CartaoIndicador({ titulo, valor, detalhe }) {
  return (
    <Cartao titulo={titulo} className="cartao-indicador">
      <strong className="valor-indicador">{valor}</strong>
      <p className="detalhe-indicador">{detalhe}</p>
    </Cartao>
  )
}
