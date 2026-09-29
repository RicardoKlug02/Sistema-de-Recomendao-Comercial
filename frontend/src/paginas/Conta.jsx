import { useState } from "react";
import Cartao from "../componentes/Cartao";
import { api } from "../servicos/api";
import { Campo, Consulta, Tabela, Etiqueta } from "../componentes/Elementos";
export function Usuarios({ usuario }) {
  const [versao, atualizar] = useState(0);
  const [erro, falhar] = useState("");
  const [ocupado, ocupar] = useState(false);
  async function alterar(id, valores) {
    ocupar(true);
    falhar("");
    try {
      await api(`/usuarios/${id}`, { method: "PATCH", body: valores });
      atualizar(versao + 1);
    } catch (e) {
      falhar(e.message);
    } finally {
      ocupar(false);
    }
  }
  return (
    <Cartao
      titulo="Gestão de acesso"
      descricao="Aprove cadastros e controle o acesso da equipe."
    >
      {erro && (
        <p role="alert" className="erro-campo">
          {erro}
        </p>
      )}
      <Consulta caminho="/usuarios" versao={versao}>
        {(usuarios) => (
          <Tabela
            colunas={["Nome", "E-mail", "Perfil", "Situação", "Ações"]}
            linhas={usuarios.map((u) => [
              u.nome,
              u.email,
              <select
                aria-label={`Perfil de ${u.nome}`}
                value={u.perfil}
                disabled={
                  ocupado || u.id === usuario.id || usuario.perfil !== "admin"
                }
                onChange={(e) => alterar(u.id, { perfil: e.target.value })}
              >
                <option value="vendedor">Vendedor</option>
                <option value="gestor">Gestor</option>
                <option value="admin">Administrador</option>
              </select>,
              <Etiqueta>
                {!u.ativo
                  ? "Inativo"
                  : u.aprovado
                    ? "Aprovado"
                    : "Aguardando aprovação"}
              </Etiqueta>,
              <div className="acoes">
                {!u.aprovado && (
                  <button
                    className="botao-secundario"
                    disabled={ocupado}
                    onClick={() => alterar(u.id, { aprovado: true })}
                  >
                    Aprovar
                  </button>
                )}
                <button
                  className="botao-secundario"
                  disabled={
                    ocupado ||
                    u.id === usuario.id ||
                    (usuario.perfil !== "admin" && u.perfil !== "vendedor")
                  }
                  onClick={() => alterar(u.id, { ativo: !u.ativo })}
                >
                  {u.ativo ? "Desativar" : "Ativar"}
                </button>
              </div>,
            ])}
          />
        )}
      </Consulta>
    </Cartao>
  );
}
export function Perfil({ usuario, aoSair }) {
  const [mensagem, informar] = useState("");
  const [erro, falhar] = useState("");
  const [ocupado, ocupar] = useState(false);
  async function salvar(e) {
    e.preventDefault();
    const form = e.currentTarget;
    const dados = Object.fromEntries(new FormData(form));
    falhar("");
    informar("");
    if (dados.senha !== dados.confirmacao) {
      falhar("As senhas não coincidem.");
      return;
    }
    ocupar(true);
    try {
      await api("/auth/senha", { method: "POST", body: dados });
      form.reset();
      informar("Senha alterada. Entre novamente para continuar.");
      aoSair();
    } catch (e) {
      falhar(e.message);
    } finally {
      ocupar(false);
    }
  }
  return (
    <div className="grade-resumos">
      <Cartao titulo="Dados da conta">
        <dl className="dados-conta">
          <dt>Nome</dt>
          <dd>{usuario.nome}</dd>
          <dt>E-mail</dt>
          <dd>{usuario.email}</dd>
          <dt>Perfil de acesso</dt>
          <dd>{usuario.perfil}</dd>
        </dl>
        <p className="aviso">
          A sessão termina ao recarregar a página ou sair da conta.
        </p>
      </Cartao>
      <Cartao titulo="Alterar senha">
        <form className="formulario-pagina" onSubmit={salvar}>
          <Campo
            rotulo="Senha atual"
            name="senha_atual"
            type="password"
            autoComplete="current-password"
            required
          />
          <Campo
            rotulo="Nova senha"
            name="senha"
            type="password"
            autoComplete="new-password"
            minLength={10}
            required
          />
          <Campo
            rotulo="Confirmar nova senha"
            name="confirmacao"
            type="password"
            autoComplete="new-password"
            minLength={10}
            required
          />
          <small>Use ao menos 10 caracteres; limite de 72 bytes.</small>
          <button className="botao-principal" disabled={ocupado}>
            {ocupado ? "Salvando…" : "Salvar nova senha"}
          </button>
          {erro && (
            <p role="alert" className="erro-campo">
              {erro}
            </p>
          )}
          {mensagem && <p role="status">{mensagem}</p>}
        </form>
      </Cartao>
    </div>
  );
}
