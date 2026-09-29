import { useEffect, useRef, useState } from 'react'
import { solicitarApi } from '../../servicos/api'

// Usa somente IDs dos produtos presentes no dossiê; o usuário escolhe a combinação.
export default function SugestoesComplementares({ produtos }) {
  const [selecionados, definirSelecionados] = useState([])
  const [resultado, definirResultado] = useState(null)
  const [erro, definirErro] = useState('')
  const [carregando, definirCarregando] = useState(false)
  const controle = useRef(null)
  useEffect(() => () => controle.current?.abort(), [])
  async function consultar() {
    if (!selecionados.length || carregando) return
    controle.current = new AbortController()
    definirCarregando(true)
    definirErro('')
    definirResultado(null)
    try {
      const retorno = await solicitarApi('/clientes/cross-selling?top_n=4', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(selecionados),
        signal: controle.current.signal,
      })
      if (!Array.isArray(retorno)) throw new Error('Não foi possível interpretar as sugestões retornadas.')
      definirResultado(retorno)
    } catch (falha) {
      if (falha.name !== 'AbortError') definirErro(falha.message)
    } finally {
      definirCarregando(false)
    }
  }
  return (
    <section className="secao-perfil" aria-labelledby="titulo-complementares">
      <h3 id="titulo-complementares">Produtos que podem complementar a compra</h3>
      <p>Selecione itens do histórico para consultar produtos comprados em conjunto.</p>
      <fieldset className="selecao-produtos" disabled={carregando}>
        <legend className="somente-leitor">Produtos de referência</legend>
        {produtos.map((produto) => (
          <label key={produto.produto_id}>
            <input
              type="checkbox"
              checked={selecionados.includes(produto.produto_id)}
              onChange={(evento) => {
                definirSelecionados((atuais) =>
                  evento.target.checked
                    ? [...atuais, produto.produto_id]
                    : atuais.filter((id) => id !== produto.produto_id),
                )
                definirResultado(null)
                definirErro('')
              }}
            />
            <span>
              {produto.nome}
              <small>SKU {produto.sku}</small>
            </span>
          </label>
        ))}
      </fieldset>
      <button className="botao-secundario" disabled={!selecionados.length || carregando} onClick={consultar}>
        {carregando ? 'Consultando…' : 'Consultar produtos complementares'}
      </button>
      {erro && (
        <p className="erro-campo" role="alert">
          {erro}
        </p>
      )}
      {resultado && (
        <div role="status">
          {resultado.length ? (
            resultado.map((produto) => (
              <article className="oportunidade-perfil" key={produto.produto_id}>
                <h4>{produto.nome}</h4>
                <p>SKU {produto.sku}</p>
                {produto.motivo && <p>{produto.motivo}</p>}
              </article>
            ))
          ) : (
            <p>Não há associações suficientes para os produtos selecionados.</p>
          )}
        </div>
      )}
    </section>
  )
}
