# Frontend — Sistema de Recomendação Comercial

SPA em React com Vite, baseada em `docs/Tela de login.png`, sem o contorno azul de seleção do desenho.

## Executar

Na pasta `frontend`, instale as dependências com `npm install` e execute `npm run dev`.
Use `npm run build` para gerar a versão de produção e `npm run lint` para verificar o código.

## Demonstração

- Digite qualquer e-mail válido e uma senha não vazia para simular o acesso.
- Campos obrigatórios, formato do e-mail, carregamento e falhas têm feedback na interface.
- Após entrar, uma confirmação permite sair e voltar ao login sem recarregar a página.
- “Esqueceu a senha?” abre a recuperação. A solicitação é simulada e nenhum e-mail é enviado.
- A sessão existe apenas em memória; recarregar retorna ao login. Senhas e tokens não são persistidos.

## Componentes e integração

- `src/components/AuthCard.jsx`: estrutura visual compartilhada.
- `src/components/FormField.jsx`: campo com label e erro acessível.
- `src/components/AuthForm.jsx`: formulário de login e recuperação, validação e carregamento.
- `src/services/auth.js`: placeholders assíncronos de login e recuperação.

Quando o contrato do backend estiver disponível, substitua `login({ email, password })` e `requestPasswordReset({ email })` pelas chamadas reais. O login deve retornar `{ user: { email } }`; falhas devem rejeitar a promessa. Autenticação e autorização reais deverão ser implementadas no servidor antes de conectar dados protegidos.

## Verificação manual

1. Enviar campos vazios e e-mail inválido; verificar mensagens e foco no primeiro campo inválido.
2. Usar e-mail válido e senha; verificar carregamento, confirmação e saída.
3. Abrir recuperação, testar e-mail inválido e concluir uma solicitação simulada; voltar ao login.
4. Navegar com Tab e Enter; verificar foco visível e ausência de rolagem horizontal no celular.
