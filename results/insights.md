# 📌 Insights do Projeto – AWS EC2 Pricing

## 💡 Insight da Matriz de Correlação
- **Preço/hora (`price_usd_hour`)** apresenta **correlação muito alta com memória (`memory_gb`)** (**0,97**) e também com vCPU (**0,78**).  
  ➡️ Isso indica que o preço é fortemente influenciado pela **quantidade de memória**, mais até do que pelo número de CPUs.  
- **Preço por vCPU (`price_per_vcpu`)** tem correlação **moderada com `memory_gb` (0,45)** e baixa com `vcpu` (0,25).  
  ➡️ Sugere que, na média, instâncias com mais memória também tendem a ter custo/vCPU maior.  
- **Preço por GB (`price_per_gb`)** praticamente **não apresenta correlação** com vCPU ou memória total, sendo muito mais volátil.

---

#### 💡 Insights sobre Outliers de Preço por Família de Instância

A análise do **preço médio por família** dentro do grupo de *outliers* revelou que:

- **Famílias `u` (Ultra Memory)** e **`p` (GPU de alta performance)** lideram com folga os valores mais altos.
  - `u` → instâncias com memória extrema, voltadas para cargas como **SAP HANA** e grandes bancos *in-memory*.
  - `p` → instâncias com GPUs potentes para **treinamento de Machine Learning**, **HPC** e simulações.
- As famílias **`u-`** chegam a ultrapassar **USD 350/hora**, valor que coincide com o ponto mais extremo visto no scatter plot de preço × vCPU.
- Outras famílias caras incluem:
  - `trn` → otimizadas para *deep learning* com AWS Trainium.
  - `x` → alta capacidade de memória para cargas especializadas.
- Famílias generalistas (`m`, `c`, `t`) **não aparecem no topo** dos preços, reforçando que os valores elevados estão ligados a **configurações especializadas e de nicho**.

---

## 💡 Insights dos Outliers de maior preço

A análise dos *scatter plots* com rótulos (`instanceType`) mostra que:

- **Topo absoluto de preço**:
  - `u7in-32tb.224xlarge` ultrapassa **USD 350/h**, confirmando o ponto mais extremo do boxplot inicial.
  
- **Cluster de altíssima capacidade** (vCPU ~900, memória 12–24 TiB):
  - `u7in-24tb.224xlarge`
  - `u7in-16tb.224xlarge`
  - `u7in-12tb.224xlarge`

- **Faixa intermediária de preço alto** (vCPU ~448, memória 12–18 TiB):
  - `u6-18tb.112xlarge`
  - `u6-24tb.112xlarge`
  - `u6-12tb.112xlarge`

- **Casos específicos de GPU e HPC**:
  - `p6-b200.48xlarge`
  - `p5.48xlarge`
  - `p5en.48xlarge`
  - Preços entre USD 50 e USD 110/h, ainda considerados outliers frente à média geral.

- **Conclusão**:
  - Os preços mais altos estão concentrados em **famílias ultra memory (`u`)** e **GPU (`p`)**.
  - As instâncias generalistas permanecem fora da faixa de outliers, reforçando que esses valores extremos estão associados a **configurações especializadas**.

---

## 💡 Insight dos Scatter Plots Rotulados (Outliers)
- **Topo absoluto de preço**: `u7in-32tb.224xlarge` (> USD 350/h).
- **Cluster de altíssima capacidade**: `u7in-24tb.224xlarge`, `u7in-16tb.224xlarge`, `u7in-12tb.224xlarge` (vCPU ~900, memória 12–24 TiB).
- **Faixa intermediária de preço alto**: `u6-18tb.112xlarge`, `u6-24tb.112xlarge`, `u6-12tb.112xlarge` (vCPU ~448, memória 12–18 TiB).
- **Casos de GPU/HPC**: `p6-b200.48xlarge`, `p5.48xlarge`, `p5en.48xlarge` (USD 50–110/h).

---

## 💡 Insight de Negócio – Modelo sem Outliers
- **R² = 0.987** → Explica 98,7% da variação nos preços para instâncias comuns.
- **MAE = 0.1204** → Erro médio de 12 centavos USD/h.
- **RMSE = 0.5309** → Baixa dispersão dos erros.  
💼 **Valor para o negócio**: previsão altamente precisa para cenários de uso comum, útil para:
  - Orçamentação precisa em projetos cloud.
  - Comparação custo-benefício por tipo/região.
  - Suporte na escolha da configuração mais econômica.

---

## 💡 Insight – Modelo com Outliers
- **R² = 0.955** → Explica 95,5% da variação.
- **MAE = 0.5204** → Erro médio 4x maior que o modelo sem outliers.
- **RMSE = 3.8907** → Grande dispersão de erros.  
📌 **Interpretação**: Outliers representam hardware altamente especializado e quebram a relação linear entre recursos e custo, levando o modelo a subestimar preços extremos.

---

## 🚀 Próximos Passos
- Desenvolver **modelo dedicado para instâncias especializadas** usando algoritmos robustos a outliers, como **XGBoost**.
- Manter dois fluxos:
  - **Modelo 1** → Previsão para uso comum (alta acurácia).
  - **Modelo 2** → Previsão para nichos de alto desempenho.
