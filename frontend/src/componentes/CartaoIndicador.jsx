import Cartao from './Cartao'
import Icone from './comercial/Icone'

export default function CartaoIndicador({
  titulo,
  valor,
  detalhe,
  icone = 'painel',
  destaque = false,
}) {
  return (
    <Cartao
      titulo={titulo}
      className={`cartao-indicador ${destaque ? 'indicador-destaque' : ''}`}
      acao={
        <span className="icone-indicador">
          <Icone nome={icone} tamanho={18} />
        </span>
      }
    >
      <strong className="valor-indicador">{valor}</strong>
      {detalhe && <p className="detalhe-indicador">{detalhe}</p>}
    </Cartao>
  )
}
