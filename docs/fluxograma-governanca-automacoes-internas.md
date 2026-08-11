# Processo de Desenvolvimento, Validação e Implantação de Automações Internas com Rastreabilidade e Controle de Auditoria

Fluxograma BPMN com raias (swimlanes) para governança de scripts e aplicações Python internas, com requisitos de rastreabilidade compatíveis com auditoria (ex.: PCI DSS).

## Visualização

Abra o arquivo HTML para visualização completa com layout corporativo:

**[fluxograma-governanca-automacoes-internas.html](./fluxograma-governanca-automacoes-internas.html)**

## Raias (Swimlanes)

| Raia | Responsabilidade |
|------|------------------|
| **Área de Negócio / Desenvolvedor** | Identificação, desenvolvimento, testes técnicos e encaminhamento |
| **Usuário da Área / Validador** | Teste de aceitação e operação |
| **TI / Segurança da Informação** | Revisão técnica, aprovação de segurança e implantação |
| **Gestor / Aprovador** | Aprovação formal da mudança |
| **Sistema de Controle (Git + GMUD)** | Versionamento e registro formal de mudanças |

## Fluxograma (Mermaid)

```mermaid
flowchart TB
    subgraph L1["🏢 Área de Negócio / Desenvolvedor"]
        E1["<b>1. Identificação da necessidade</b><br/>• Atividade manual identificada<br/>• Objetivo, benefício e escopo<br/>• Avaliar dados sensíveis / ambiente crítico"]
        E2["<b>2. Desenvolvimento</b><br/>• Criar script/aplicação Python<br/>• Código no Git (v1.0.0)<br/>• Documentação básica"]
        E3["<b>3. Testes técnicos</b><br/>• Cenários positivos e negativos<br/>• Evidências registradas"]
        E4A["<b>4. Encaminhamento</b><br/>• Enviar formulário de teste ao usuário"]
        E7D["<b>7. Aprovação — Desenvolvedor</b>"]
        E10["<b>10. Correções e novas versões</b><br/>• v1.0.0 → v1.0.1<br/>• Git + CHANGELOG + GMUD<br/>• Sem substituição sem rastreio"]
    end

    subgraph L2["👤 Usuário da Área / Validador"]
        E4B["<b>4. Teste de aceitação</b><br/>• Testes reais<br/>• Formulário por e-mail<br/>• Evidência para GMUD"]
        E9["<b>9. Operação e monitoramento</b><br/>• Uso em produção<br/>• Logs: usuário, data, arquivos, resultado"]
    end

    subgraph L3["🔒 TI / Segurança da Informação"]
        E5["<b>5. Revisão e avaliação</b><br/>• Código, permissões, instalação<br/>• Riscos e impacto"]
        E7R["<b>7. Aprovação — Revisor</b>"]
        E8["<b>8. Implantação</b><br/>• Instalar versão aprovada<br/>• Permissões adequadas<br/>• Registrar local e versão"]
    end

    subgraph L4["✅ Gestor / Aprovador"]
        E7G["<b>7. Aprovação — Gestor</b><br/>Dev → Revisor → Gestor → TI/Sec*<br/>*Quando aplicável"]
    end

    subgraph L5["📋 Sistema de Controle (Git + GMUD)"]
        E6["<b>6. Abertura da GMUD</b><br/>• Objetivo, versão, responsável<br/>• Testes, rollback, riscos<br/>• Anexos: docs + aprovações"]
    end

    subgraph AUDIT["🛡️ Evidências para Auditoria"]
        A1["Código no Git"]
        A2["CHANGELOG"]
        A3["Versão identificada"]
        A4["Testes"]
        A5["Aprovação usuário"]
        A6["GMUD aprovada"]
        A7["Registro implantação"]
        A8["Controle de acesso"]
    end

    E1 --> E2 --> E3 --> E4A --> E4B --> E5 --> E6
    E6 --> E7D --> E7R --> E7G --> E8 --> E9 --> E10
    E10 -.->|Nova versão| E2

    E2 -.-> A1
    E10 -.-> A2
    E6 -.-> A3
    E3 -.-> A4
    E4B -.-> A5
    E7G -.-> A6
    E8 -.-> A7
    E5 -.-> A8

    style L1 fill:#ebf4ff,stroke:#1e3a5f
    style L2 fill:#f0f7ff,stroke:#3182ce
    style L3 fill:#b2f5ea,stroke:#285e61
    style L4 fill:#e9d8fd,stroke:#553c9a
    style L5 fill:#edf2f7,stroke:#4a5568
    style AUDIT fill:#c6f6d5,stroke:#276749
```

## Resumo das etapas

1. **Identificação** — Documentar necessidade e avaliar sensibilidade dos dados.
2. **Desenvolvimento** — Código Python versionado no Git com documentação.
3. **Testes técnicos** — Validação com evidências (positivo/negativo/erro).
4. **Aceitação do usuário** — Formulário de teste real com retorno por e-mail.
5. **Revisão técnica** — TI/Security avalia código, permissões e riscos.
6. **GMUD** — Mudança formal com anexos e plano de rollback.
7. **Aprovação** — Cadeia: Desenvolvedor → Revisor → Gestor → TI/Security.
8. **Implantação** — Versão aprovada instalada com registro.
9. **Operação** — Uso monitorado com logs quando aplicável.
10. **Evolução** — Nova versão sempre com rastreabilidade completa.

## Evidências para auditoria

- Código-fonte versionado no Git
- Histórico de alterações (CHANGELOG)
- Versão identificada (tag/release)
- Testes realizados (técnico + aceitação)
- Aprovação formal do usuário
- GMUD aprovada e arquivada
- Registro de implantação
- Controle de acesso e permissões
