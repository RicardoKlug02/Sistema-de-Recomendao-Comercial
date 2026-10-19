import { useEffect, useState } from 'react'
import { MemoriaPaginas } from '../servicos/estadoPaginas'
import Importacao from './Importacao'
import Clientes from './Clientes'
import Alertas from './Alertas'
import Usuarios from './Usuarios'
import VisaoGeral from './VisaoGeral'
import Relatorios from './Relatorios'
import AnaliseSistema from './AnaliseSistema'
import RegrasNegocio from './RegrasNegocio'
import MenuLateral from '../componentes/MenuLateral'
import useDados from '../servicos/useDados'
import './PainelComercial.css'
import './Operacao.css'
import './Usabilidade.css'

const secoes = {
  painel: 'Visão geral',
  clientes: 'Clientes',
  alertas: 'Alertas',
  importacoes: 'Importação',
  usuarios: 'Usuários',
  relatorios: 'Relatórios',
  analise: 'Análise do sistema',
  regras: 'Regras de negócio',
}

// O shell coordena navegação e invalidação das consultas após uma importação confirmada.
export default function PainelComercial({ usuario, aoSair, referenciaTitulo }) {
  const [secao, definirSecao] = useState('painel')
  const [clienteId, definirCliente] = useState(null)
  const [memoria] = useState(() => new Map())
  const [retorno, definirRetorno] = useState(null)
  const [versao, definirVersao] = useState(0)
  const cadastroVendedores = useDados('/comercial/vendedores', versao)
  const cadastroFabricas = useDados('/comercial/fabricas', versao)
  const atualizar = () => definirVersao((v) => v + 1)
  const gestor = ['admin', 'gestor'].includes(usuario.perfil)
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
  useEffect(() => {
    document.title = `${secoes[secao]} | Rio Verde Representações`
    document.querySelector('.conteudo-painel h1')?.focus()
  }, [secao])
  return (
    <MemoriaPaginas.Provider value={memoria}><div className="estrutura-painel">
      <a
        className="atalho-conteudo"
        href="#conteudo"
        onClick={(e) => {
          e.preventDefault()
          document.querySelector('.conteudo-painel h1')?.focus()
        }}
      >
        Pular para o conteúdo
      </a>
      <MenuLateral
        usuario={usuario}
        aoSair={aoSair}
        secaoAtiva={secao}
        aoNavegar={navegar}
      />
      <div className="barra-superior">
        <span>
          Rio Verde <span>/</span> {secoes[secao]}
        </span>
        <span>
          {new Date().toLocaleDateString('pt-BR', {
            day: 'numeric',
            month: 'long',
            year: 'numeric',
          })}
        </span>
      </div>
      {(cadastroVendedores.erro || cadastroFabricas.erro) && <aside className="aviso-catalogos" role="alert"><p>Não foi possível carregar os vendedores ou fábricas.</p><button className="botao-secundario" onClick={() => { cadastroVendedores.tentarNovamente(); cadastroFabricas.tentarNovamente() }}>Tentar novamente</button></aside>}
      {secao === 'painel' && (
        <VisaoGeral
          vendedores={cadastroVendedores.dados || []}
          fabricas={cadastroFabricas.dados || []}
          erroVendedores={cadastroVendedores.erro}
          versao={versao}
          aoAtualizar={atualizar}
          aoAbrirCliente={abrirCliente}
          aoAbrirAlertas={() => navegar('alertas')}
          referenciaTitulo={referenciaTitulo}
        />
      )}
      {secao === 'importacoes' && gestor && (
        <Importacao usuario={usuario} aoImportar={atualizar} />
      )}
      {secao === 'clientes' && (
        <Clientes key={clienteId || 'lista'} inicial={clienteId} fabricaInicial={retorno?.fabrica} origem={retorno?.secao}
          aoVoltar={retorno ? () => { definirCliente(null); definirSecao(retorno.secao); definirRetorno(null) } : null}
          fabricas={cadastroFabricas.dados || []} />
      )}
      {secao === 'alertas' && (
        <Alertas
          fabricas={cadastroFabricas.dados || []}
          vendedores={cadastroVendedores.dados || []}
          aoAbrirCliente={abrirCliente}
        />
      )}
      {secao === 'usuarios' && gestor && <Usuarios />}
      {secao === 'relatorios' && <Relatorios fabricas={cadastroFabricas.dados || []} vendedores={cadastroVendedores.dados || []} />}
      {secao === 'regras' && <RegrasNegocio fabricas={cadastroFabricas.dados || []} vendedores={cadastroVendedores.dados || []} gestor={gestor} aoAlterar={atualizar} />}
      {secao === 'analise' && <AnaliseSistema fabricas={cadastroFabricas.dados || []} vendedores={cadastroVendedores.dados || []} />}
    </div></MemoriaPaginas.Provider>
  )
}
