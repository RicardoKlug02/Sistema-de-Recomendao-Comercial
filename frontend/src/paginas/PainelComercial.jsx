import { useEffect, useState } from 'react'
import { MemoriaPaginas } from '../hooks/estadoPaginas'
import useDados from '../hooks/useDados'
import MenuLateral from '../componentes/layout/MenuLateral'
import Alertas from './Alertas'
import AnaliseSistema from './AnaliseSistema'
import Clientes from './Clientes'
import Importacao from './Importacao'
import RegrasNegocio from './RegrasNegocio'
import Relatorios from './Relatorios'
import Usuarios from './Usuarios'
import VisaoGeral from './VisaoGeral'
import { tituloDocumento, tituloSecao } from '../secoes'
import { ehGestor } from '../servicos/autenticacao'

export default function PainelComercial({ usuario, aoSair }) {
  const gestor = ehGestor(usuario)
  const [secao, definirSecao] = useState(gestor ? 'painel' : 'alertas')
  const [clienteId, definirCliente] = useState(null)
  const [memoria] = useState(() => new Map())
  const [retorno, definirRetorno] = useState(null)
  const [versao, definirVersao] = useState(0)
  const cadastroVendedores = useDados('/comercial/vendedores', versao)
  const vendedores = cadastroVendedores.dados || []
  const cadastroFabricas = useDados('/comercial/fabricas', versao)
  const fabricas = cadastroFabricas.dados || []
  const cadastros = { vendedores, fabricas }
  const atualizar = () => definirVersao((v) => v + 1)
  const tituloAtual = secao === 'alertas' && !gestor ? 'Hoje' : tituloSecao(secao)

  function abrirCliente(id, contexto = {}) {
    definirRetorno({ secao, fabrica: contexto.fabrica ?? '' })
    definirCliente(id)
    definirSecao('clientes')
  }
  function navegar(destino) {
    definirRetorno(null)
    if (destino === 'clientes') definirCliente(null)
    definirSecao(destino)
  }

  useEffect(() => { document.title = tituloDocumento(tituloAtual) }, [tituloAtual])

  return (
    <MemoriaPaginas.Provider value={memoria}><div className="estrutura-painel">
      <a className="atalho-conteudo" href="#titulo-pagina" onClick={(e) => { e.preventDefault(); document.getElementById('titulo-pagina')?.focus() }}>
        Pular para o conteúdo
      </a>
      <MenuLateral usuario={usuario} gestor={gestor} aoSair={aoSair} secaoAtiva={secao} aoNavegar={navegar} />
      <div className="barra-superior">
        <span>Rio Verde <span>/</span> {tituloAtual}</span>
        <span>{new Date().toLocaleDateString('pt-BR', { dateStyle: 'long' })}</span>
      </div>
      {(cadastroVendedores.erro || cadastroFabricas.erro) && <aside className="aviso-catalogos" role="alert"><p>Não foi possível carregar os vendedores ou fábricas.</p><button className="botao-secundario" onClick={() => { cadastroVendedores.tentarNovamente(); cadastroFabricas.tentarNovamente() }}>Tentar novamente</button></aside>}
      {secao === 'painel' && <VisaoGeral {...cadastros} versao={versao} aoAtualizar={atualizar} aoAbrirCliente={abrirCliente} aoAbrirAlertas={() => navegar('alertas')} />}
      {secao === 'clientes' && <Clientes key={clienteId || 'lista'} inicial={clienteId} fabricaInicial={retorno?.fabrica} origem={retorno?.secao}
        aoVoltar={retorno ? () => { definirCliente(null); definirSecao(retorno.secao); definirRetorno(null) } : null}
        fabricas={fabricas} />}
      {secao === 'alertas' && <Alertas {...cadastros} rotina={!gestor} aoAbrirCliente={abrirCliente} />}
      {secao === 'relatorios' && <Relatorios {...cadastros} />}
      {secao === 'analise' && <AnaliseSistema {...cadastros} />}
      {secao === 'regras' && <RegrasNegocio {...cadastros} gestor={gestor} aoAlterar={atualizar} />}
      {secao === 'importacoes' && gestor && <Importacao aoImportar={atualizar} />}
      {secao === 'usuarios' && gestor && <Usuarios />}
    </div></MemoriaPaginas.Provider>
  )
}
