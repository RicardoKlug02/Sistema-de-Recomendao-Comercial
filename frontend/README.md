# Interface comercial

React + Vite integrado à API FastAPI. O login exige uma conta aprovada; a sessão JWT fica no sessionStorage da aba.

## Desenvolvimento

```sh
npm ci
npm run dev
```

Inicie a API na porta 8000. O proxy do Vite encaminha /api para localhost:8000. Para outro servidor, use VITE_API_URL conforme .env.example.

## Verificação e produção

```sh
npm run lint
npm run build
```

O backend serve frontend/dist quando SERVE_FRONTEND=true. O Dockerfile na raiz realiza o build e publica interface e API juntas.

O menu oferece Dashboard, Clientes 360º, Alertas e Importação. Administradores também aprovam cadastros em Usuários. Os dados vêm das planilhas importadas, sem métricas demonstrativas. Recomendações só aparecem quando há histórico de itens suficiente.

Veja ../docs/IMPLANTACAO.md para configuração de Neon/Render, regras de importação e inatividade.
