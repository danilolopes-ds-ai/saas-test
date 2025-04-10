# Contribuindo com o SaaS Atendimento Flui

Obrigado pelo interesse em contribuir com o projeto! Aqui estão algumas diretrizes para ajudar no processo.

## Princípios fundamentais

1. Simples é melhor que complexo - busque sempre a solução mais clara e direta.
2. Desenvolva de forma modular - crie componentes independentes e reutilizáveis.
3. Evite código hardcode ou engessado - prefira soluções flexíveis e configuráveis.
4. Priorize sempre a preservação da estrutura existente do código. Não altere nada desnecessariamente.
5. Trabalhe em equipe - discuta mudanças significativas antes de implementá-las.
6. Use arquitetura limpa e princípios SOLID para manter o sistema robusto e flexível.

## Fluxo de trabalho

1. Faça um fork do repositório
2. Clone seu fork: `git clone https://github.com/seu-usuario/saas-test.git`
3. Crie uma branch para sua feature: `git checkout -b feature/nome-da-feature`
4. Faça suas alterações seguindo os padrões do projeto
5. Adicione testes para suas alterações quando aplicável
6. Execute os testes para garantir que tudo está funcionando
7. Faça commit das suas alterações: `git commit -m "Adiciona nova funcionalidade"`
8. Envie para o GitHub: `git push origin feature/nome-da-feature`
9. Abra um Pull Request para a branch principal

## Padrões de código

- Escreva código em inglês
- Use snake_case para variáveis e métodos
- Use PascalCase para classes
- Documente adequadamente qualquer nova funcionalidade ou alteração significativa
- Siga o estilo de código existente no projeto

## Restrições importantes

- Não altere o schema.prisma sem explicação e permissão prévia
- Não instale ou desinstale módulos sem permissão
- No ambiente de desenvolvimento, use apenas serviços locais
- Não implemente regras de negócio não solicitadas sem aprovação prévia
- Não altere arquivos não relacionados à sua tarefa sem justificativa

## Relatando bugs

Se você encontrar um bug, por favor, abra uma issue com as seguintes informações:

- Descrição clara do problema
- Passos para reproduzir
- Comportamento esperado
- Screenshots (se aplicável)
- Ambiente (sistema operacional, navegador, etc.)

## Sugerindo melhorias

Sugestões de melhorias são sempre bem-vindas! Abra uma issue com sua sugestão, incluindo:

- Descrição clara da melhoria
- Benefícios esperados
- Possíveis abordagens para implementação
