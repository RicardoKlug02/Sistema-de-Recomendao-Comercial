import { useState } from "react";
import { api, definirToken } from "../servicos/api";
import { Campo } from "../componentes/Elementos";
export default function Acesso({ rota, aoEntrar, aviso }) {
  const modo = rota.split("?")[0];
  const [erro, falhar] = useState("");
  const [mensagem, informar] = useState("");
  const [ocupado, ocupar] = useState(false);
  const titulos = {
    entrar: "Bem-vindo de volta",
    cadastro: "Solicitar acesso",
    recuperar: "Recuperar senha",
    redefinir: "Criar nova senha",
  };
  async function enviar(e) {
    e.preventDefault();
    falhar("");
    informar("");
    ocupar(true);
    const dados = Object.fromEntries(new FormData(e.currentTarget));
    try {
      if (modo === "entrar") {
        const r = await api("/auth/login", {
          method: "POST",
          body: new URLSearchParams({
            username: dados.email,
            password: dados.senha,
          }),
        });
        definirToken(r.access_token);
        aoEntrar({
          id: r.usuario_id,
          nome: r.usuario_nome,
          email: r.usuario_email,
          perfil: r.usuario_perfil,
        });
      } else if (modo === "cadastro") {
        const r = await api("/auth/registrar", { method: "POST", body: dados });
        informar(r.mensagem);
      } else if (modo === "recuperar") {
        const r = await api("/auth/recuperar", { method: "POST", body: dados });
        informar(r.mensagem);
      } else {
        if (dados.senha !== dados.confirmacao)
          throw new Error("As senhas não coincidem.");
        const token = new URLSearchParams(rota.split("?")[1]).get("token");
        await api("/auth/redefinir", {
          method: "POST",
          body: { senha: dados.senha, token },
        });
        informar("Senha atualizada. Você já pode entrar.");
      }
    } catch (e) {
      falhar(e.message);
    } finally {
      ocupar(false);
    }
  }
  return (
    <main className="pagina-acesso">
      <section className="apresentacao-acesso">
        <a className="marca" href="#/entrar">
          ▥ Rio Verde <small>REPRESENTAÇÕES</small>
        </a>
        <p className="sobretitulo">INTELIGÊNCIA COMERCIAL</p>
        <h1>
          Conheça seus clientes.
          <br />
          Encontre a próxima oportunidade.
        </h1>
        <p>
          Histórico, recomendações e indicadores para preparar cada visita com
          informação.
        </p>
      </section>
      <section className="form-acesso">
        <p className="sobretitulo">SUA ÁREA COMERCIAL</p>
        <h2>{titulos[modo] || titulos.entrar}</h2>
        <p>
          {modo === "cadastro"
            ? "Seu cadastro será analisado por um administrador."
            : "Acesse com o e-mail cadastrado na plataforma."}
        </p>
        {aviso && (
          <p className="aviso" role="status">
            {aviso}
          </p>
        )}
        <form className="formulario-pagina" onSubmit={enviar}>
          {!mensagem && (
            <>
              {modo === "cadastro" && (
                <Campo
                  rotulo="Nome completo"
                  name="nome"
                  autoComplete="name"
                  minLength={2}
                  maxLength={100}
                  required
                />
              )}
              {modo !== "redefinir" && (
                <Campo
                  rotulo="E-mail"
                  name="email"
                  type="email"
                  autoComplete="username"
                  required
                />
              )}
              {modo !== "recuperar" && (
                <Campo
                  rotulo={modo === "redefinir" ? "Nova senha" : "Senha"}
                  name="senha"
                  type="password"
                  autoComplete={
                    modo === "entrar" ? "current-password" : "new-password"
                  }
                  minLength={modo === "entrar" ? 1 : 10}
                  required
                />
              )}
              {modo === "redefinir" && (
                <Campo
                  rotulo="Confirmar senha"
                  name="confirmacao"
                  type="password"
                  autoComplete="new-password"
                  required
                />
              )}
              {["cadastro", "redefinir"].includes(modo) && (
                <small>Ao menos 10 caracteres, até 72 bytes.</small>
              )}
              <button className="botao-principal" disabled={ocupado}>
                {ocupado
                  ? "Aguarde…"
                  : {
                      entrar: "Entrar na plataforma",
                      cadastro: "Solicitar cadastro",
                      recuperar: "Enviar link de recuperação",
                      redefinir: "Salvar senha",
                    }[modo] || "Entrar"}
              </button>
            </>
          )}
          {erro && (
            <p role="alert" className="erro-campo">
              {erro}
            </p>
          )}
          {mensagem && (
            <p role="status" className="aviso">
              {mensagem}
            </p>
          )}
        </form>
        <div className="links-acesso">
          {modo === "entrar" ? (
            <>
              <a href="#/recuperar">Esqueceu sua senha?</a>
              <a href="#/cadastro">Solicitar acesso →</a>
            </>
          ) : (
            <a href="#/entrar">← Voltar para entrar</a>
          )}
        </div>
      </section>
    </main>
  );
}
