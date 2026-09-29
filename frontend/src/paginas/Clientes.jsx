import { useState } from 'react'
import CabecalhoPagina from '../componentes/comercial/CabecalhoPagina'
import FiltrosCarteira from '../componentes/comercial/FiltrosCarteira'
import CartaoCliente from '../componentes/comercial/CartaoCliente'
import EstadoVazio from '../componentes/comercial/EstadoVazio'
import EstadoConsulta from '../componentes/comercial/EstadoConsulta'
import { adaptarCliente } from '../servicos/dadosComerciais'
import useConsulta from '../ganchos/useConsulta'

export default function Clientes({ versao, aoAtualizar, aoAbrirCliente }) {
  const [busca, definirBusca] = useState('')
  const [ordem, definirOrdem] = useState('nome')
  const termo = busca.trim()
  const consulta = useConsulta(
    termo.length >= 2 ? `/clientes/busca?termo=${encodeURIComponent(termo)}` : null,
    versao,
  )
  const formatoInvalido = consulta.dados !== null && !Array.isArray(consulta.dados)
  const clientes = (Array.isArray(consulta.dados) ? consulta.dados.map(adaptarCliente) : []).sort(
    (a, b) =>
      (ordem === 'cidade' ? (a.cidade || '').localeCompare(b.cidade || '', 'pt-BR') : 0) ||
      a.nome.localeCompare(b.nome, 'pt-BR'),
  )
  return (
    <main className="conteudo-painel">
      <CabecalhoPagina
        titulo="Cada cliente, uma relação."
        descricao="Busque na sua base e abra o perfil para conhecer o histórico de compras."
        identificador="titulo-clientes"
      />
      <FiltrosCarteira
        busca={busca}
        aoBuscar={definirBusca}
        rotulo="Buscar cliente"
        dica="Razão social, nome fantasia ou CNPJ/CPF"
        campos={[
          {
            nome: 'ordem',
            titulo: 'Ordenar resultados',
            valor: ordem,
            aoAlterar: definirOrdem,
            opcoes: [
              { valor: 'nome', rotulo: 'Nome do cliente' },
              { valor: 'cidade', rotulo: 'Cidade' },
            ],
          },
        ]}
      />
      <p className="contagem-resultados contagem-busca" role="status">
        {termo.length < 2
          ? 'Digite pelo menos dois caracteres para consultar a base.'
          : consulta.carregando
            ? 'Buscando clientes…'
            : consulta.erro || formatoInvalido
              ? 'Busca não concluída.'
              : `${clientes.length} resultados retornados para esta busca.`}
      </p>
      <EstadoConsulta
        {...consulta}
        erro={
          consulta.erro ||
          (formatoInvalido ? 'Não foi possível interpretar os clientes retornados pelo servidor.' : '')
        }
        aoTentar={aoAtualizar}
      />
      {termo.length < 2 ? (
        <EstadoVazio
          titulo="Encontre seu próximo contato"
          descricao="Pesquise pelo nome ou documento do cliente. A consulta retorna os resultados encontrados, não uma listagem completa da carteira."
        />
      ) : (
        !consulta.carregando &&
        !consulta.erro &&
        !formatoInvalido &&
        (clientes.length ? (
          <div className="grade-clientes">
            {clientes.map((cliente) => (
              <CartaoCliente key={cliente.id} cliente={cliente} aoAbrirCliente={aoAbrirCliente} />
            ))}
          </div>
        ) : (
          <EstadoVazio
            titulo="Nenhum cliente encontrado"
            descricao="Tente outro trecho do nome ou o CNPJ/CPF completo."
          />
        ))
      )}
      <p className="nota-painel">
        A busca retorna um conjunto limitado de resultados. Refine o nome ou informe o documento completo para
        localizar um cliente específico.
      </p>
    </main>
  )
}
