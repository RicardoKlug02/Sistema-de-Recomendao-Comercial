# Cadastro e aprovação por e-mail

## O que foi corrigido

- Funções ausentes de geração e validação do token de aprovação e compatibilidade do decodificador de login.
- Inicialização do e-mail somente no envio: configuração ausente não derruba a API nem o login.
- Tempo de espera limitado, erros de envio tratados como HTTP 503 e registro do tipo de falha, sem expor tokens ou credenciais.
- Reenvio pelo mesmo `POST /api/v1/auth/registrar`: uma conta ativa e pendente só pode retomar a solicitação com a senha original. Nome, senha e perfil não são substituídos. Contas aprovadas ou desativadas não podem usar esse fluxo.
- Conteúdo informado pelo usuário escapado no HTML do e-mail.
- Opção de envio via HTTPS com Resend, mantendo SMTP para ambientes que permitem esse protocolo.

Não foi confirmado o motivo exato do erro na instância publicada, pois seus logs não estão disponíveis neste projeto. O código local não corresponde necessariamente à versão atualmente publicada.

## Configurar no Render

O [Render gratuito bloqueia as portas SMTP 25, 465 e 587](https://render.com/docs/free). Nesse ambiente, configure o envio via HTTPS. A implementação usa a [API de envio do Resend](https://resend.com/docs/api-reference/emails/send-email).

No serviço do backend, em **Environment**, configure:

| Variável | Valor |
| --- | --- |
| `EMAIL_PROVEDOR` | `resend` |
| `RESEND_API_KEY` | Chave de envio criada na conta do Resend |
| `MAIL_FROM` | Endereço de e-mail autorizado pelo provedor, sem nome de exibição |
| `ADMIN_EMAIL` | E-mail real do administrador que aprovará as contas |
| `BACKEND_URL` | `https://sistema-de-recomendao-comercial.onrender.com` |

O remetente precisa atender às regras de domínio verificado do provedor. Remetentes de teste podem restringir os destinatários; confirme que o administrador pode receber o e-mail. Configure credenciais exclusivamente no backend, nunca em variáveis `VITE_*` ou no Git.

Preserve as chaves de segurança existentes (`CHAVE_SERIALIZER`, `JWT_SECRET_KEY`, `SECRET_KEY`, `SECRET_ENCRYPTION_KEY`) e a configuração do banco. Não gere uma nova chave de criptografia para corrigir o envio: isso comprometeria a leitura dos dados existentes. O backend usa Python 3.11 ou superior.

Para SMTP em ambiente compatível, mantenha `EMAIL_PROVEDOR=smtp` e configure `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM`, `MAIL_SERVER`, `MAIL_PORT`, `MAIL_STARTTLS` e `MAIL_SSL_TLS`. Use credenciais autorizadas pelo provedor.

## Publicar e confirmar

1. Publique a versão corrigida na branch conectada ao serviço e faça o deploy no Render, após configurar o provedor.
2. Abra `/docs` e envie `POST /api/v1/auth/registrar` com nome, e-mail e senha. Se a conta foi salva durante a falha anterior, use a mesma senha. Sem a senha original, contate o administrador; esta rota não redefine senhas.
3. HTTP **201** indica que o provedor aceitou o e-mail, não uma garantia de entrega na caixa de entrada. O administrador deve conferir sua caixa de entrada e spam.
4. O administrador abre o link recebido, válido por 48 horas. Só depois disso o usuário consegue fazer login. Caso um link antigo seja incompatível com a versão publicada ou tenha expirado, repita o cadastro com as mesmas credenciais para gerar outro.
5. HTTP **503** significa que a conta permanece salva e pendente, mas o envio não foi confirmado. Verifique configuração e logs antes de repetir. Se houver timeout, o provedor ainda pode ter aceitado a mensagem.
6. HTTP **400** indica que não é possível retomar com esses dados; HTTP **422** indica dados inválidos. Outros erros devem ser investigados nos logs do serviço.

A aprovação não aumenta o perfil: contas novas continuam como vendedor. Importações exigem gestor ou admin.

## Validação local

```bash
python -m pytest tests/test_autenticacao_email.py tests/test_api.py tests/test_seguranca.py -q
```

Os testes usam banco em memória, segredos exclusivos de teste e transporte de e-mail simulado. Cobrem cadastro, erro SMTP, HTTPS, configuração ausente, retomada sem duplicação, senha incorreta, aprovação, link inválido/expirado e login. Nenhum e-mail real é enviado.
