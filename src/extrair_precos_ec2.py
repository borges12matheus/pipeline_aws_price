import os, json, argparse
import boto3
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ---- helpers ---------------------------------------------------------------
def _first(d):  # Função auxiliar para pegar o primeiro value de um dict
    return next(iter(d.values())) if isinstance(d, dict) and d else None

def parse_memory_gb(mem_str):
    # Transformando os dados de memória em numérico e padronizando em Gib. Exemplos: "8 GiB", "64 GiB", "12288 MiB"
    if not mem_str: return None
    s = mem_str.replace(",", "").strip().lower()
    if "gib" in s:
        return float(s.split("gib")[0].strip())
    if "mib" in s:
        return float(s.split("mib")[0].strip())/1024.0
    try:
        return float(s)
    except:
        return None

def parse_vcpu(vcpu_str):
    # Transformando os dados de vcpu para numérico
    try:
        return float(vcpu_str) if vcpu_str else None
    except:
        return None

def get_on_demand_price_usd(item):
    # Filtrando os dados do tipo "OnDemand"(sob demanda)
    terms = item.get("terms", {}).get("OnDemand", {})
    t = _first(terms)
    if not t: return None, None
    
    # Filtrando o "priceDimensions" por preço por hora de uso
    for dim in t.get("priceDimensions", {}).values():
        if dim.get("unit", "").lower() == "hrs":
            price = dim.get("pricePerUnit", {}).get("USD")
            try:
                return float(price), "Hrs"
            except:
                return None, "Hrs"
    # Se não encontrar unidade em horas retorna vazio
    return None, None

# ---- coleta ----------------------------------------------------------------
def fetch_ec2_linux_shared(client, regions=None, max_pages=200):
    """
    Coleta produtos EC2 On-Demand Linux/Shared. Se regions é None, pega tudo.
    """
    base_filters = [
        {"Type":"TERM_MATCH","Field":"operatingSystem","Value":"Linux"},
        {"Type":"TERM_MATCH","Field":"tenancy","Value":"Shared"},
        {"Type":"TERM_MATCH","Field":"preInstalledSw","Value":"NA"},
        {"Type":"TERM_MATCH","Field":"capacitystatus","Value":"Used"},
    ]

    produtos = []
    if regions:
        # faz uma chamada por região
        for reg in regions:
            next_token = None
            pages = 0
            while True:
                params = {
                    "ServiceCode":"AmazonEC2",
                    "FormatVersion":"aws_v1",
                    "MaxResults":100,
                    "Filters": base_filters + [
                        {"Type":"TERM_MATCH","Field":"regionCode","Value":reg}
                    ]
                }
                if next_token: params["NextToken"] = next_token
                resp = client.get_products(**params)
                for p in resp.get("PriceList", []):
                    produtos.append(json.loads(p))
                next_token = resp.get("NextToken")
                pages += 1
                if not next_token or pages >= max_pages:
                    break
    else:
        # sem filtro de região
        next_token = None
        pages = 0
        while True:
            params = {
                "ServiceCode":"AmazonEC2",
                "FormatVersion":"aws_v1",
                "MaxResults":100,
                "Filters": base_filters
            }
            if next_token: params["NextToken"] = next_token
            resp = client.get_products(**params)
            for p in resp.get("PriceList", []):
                produtos.append(json.loads(p))
            next_token = resp.get("NextToken")
            pages += 1
            if not next_token or pages >= max_pages:
                break

    return produtos

# ---- normalização ----------------------------------------------------------
def normalize_df(produtos):
    rows = []
    for it in produtos:
        prod = it.get("product", {})
        attrs = prod.get("attributes", {})
        # mantem apenas items com instanceType (ignora data transfer, storage etc.)
        if not attrs.get("instanceType"):
            continue

        price, unit = get_on_demand_price_usd(it)
        if price is None:  # sem preço, ignora
            continue

        vcpu = parse_vcpu(attrs.get("vcpu"))
        mem_gb = parse_memory_gb(attrs.get("memory"))

        rows.append({
            "sku": prod.get("sku"),
            "instanceType": attrs.get("instanceType"),
            "family": (attrs.get("instanceType") or "").split(".")[0],
            "regionCode": attrs.get("regionCode"),
            "location": attrs.get("location"),
            "operatingSystem": attrs.get("operatingSystem"),
            "tenancy": attrs.get("tenancy"),
            "vcpu": vcpu,
            "memory_gb": mem_gb,
            "price_usd_hour": price,
            "unit": unit
        })

    df = pd.DataFrame(rows).drop_duplicates()
    # métricas úteis
    df["price_per_vcpu"] = df.apply(lambda r: r["price_usd_hour"]/r["vcpu"] if r["vcpu"] and r["vcpu"]>0 else None, axis=1)
    df["price_per_gb"]   = df.apply(lambda r: r["price_usd_hour"]/r["memory_gb"] if r["memory_gb"] and r["memory_gb"]>0 else None, axis=1)
    return df

# ---- main ------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Extrai preços EC2 On-Demand Linux/Shared e salva CSV.")
    parser.add_argument("--regions", nargs="*", default=["us-east-1","sa-east-1","eu-west-1"],
                        help="Lista de regiões (ex: us-east-1 sa-east-1). Vazio = todas.")
    parser.add_argument("--out", default="data/custos_aws_ec2_on_demand.csv", help="Caminho do CSV de saída.")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    client = boto3.client("pricing", region_name=os.getenv("AWS_DEFAULT_REGION","us-east-1"))

    print(f"Coletando EC2 On-Demand Linux/Shared para regiões: {args.regions or 'todas'}")
    produtos = fetch_ec2_linux_shared(client, regions=args.regions or None)
    print(f"Itens brutos: {len(produtos)}")

    df = normalize_df(produtos)
    print(f"Linhas após normalização: {len(df)}")
    if len(df) == 0:
        print("⚠️ Nenhum dado coletado. Verifique permissões/filters.")
        return

    df.to_csv(args.out, index=False)
    print(f"✅ CSV salvo em: {args.out}")

def run_extract(regions=None, out_path="data/custos_aws_ec2_on_demand_sem_filtro.csv"):
    client = boto3.client("pricing", region_name=os.getenv("AWS_DEFAULT_REGION","us-east-1"))
    produtos = fetch_ec2_linux_shared(client, regions=regions or ["us-east-1","sa-east-1","eu-west-1"])
    df = normalize_df(produtos)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    return df


if __name__ == "__main__":
    main()
