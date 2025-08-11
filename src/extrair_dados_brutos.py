# raw_extract_pricing.py
import os, json
import boto3
import pandas as pd
from typing import List, Optional

def extract_pricing_raw(
    service_code: str = "AmazonEC2",
    regions: Optional[List[str]] = None,       # ex.: ["us-east-1","sa-east-1"]
    max_pages: int = 500,
    output_path: str = "data/raw_aws_pricing.parquet",
    output_format: str = "parquet",            # "parquet" ou "csv"
    extra_filters: Optional[List[dict]] = None # filtros opcionais (TERM_MATCH)
):
    """
    Coleta itens brutos (PriceList) da AWS Pricing API e salva em CSV/Parquet.
    Cada linha contém o SKU, regionCode (se existir) e o JSON bruto em 'raw_json'.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    client = boto3.client("pricing", region_name="us-east-1")  # Pricing é us-east-1
    base = {
        "ServiceCode": service_code,
        "FormatVersion": "aws_v1",
        "MaxResults": 100,
    }

    filtros_base = extra_filters[:] if extra_filters else []

    def _fetch(params):
        items = []
        next_token = None
        pages = 0
        while True:
            if next_token:
                params["NextToken"] = next_token
            resp = client.get_products(**params)
            items.extend(resp.get("PriceList", []))
            next_token = resp.get("NextToken")
            pages += 1
            if not next_token or pages >= max_pages:
                break
        return items

    all_rows = []

    if regions:  # faz uma chamada por região (mais previsível)
        for reg in regions:
            params = dict(base)
            params["Filters"] = filtros_base + [
                {"Type": "TERM_MATCH", "Field": "regionCode", "Value": reg}
            ]
            raw_items = _fetch(params)
            for s in raw_items:
                try:
                    obj = json.loads(s)
                except Exception:
                    obj = {}
                prod = obj.get("product", {})
                attrs = prod.get("attributes", {})
                sku = prod.get("sku")
                region = attrs.get("regionCode")
                all_rows.append({"sku": sku, "regionCode": region, "raw_json": s})
    else:
        params = dict(base)
        if filtros_base:
            params["Filters"] = filtros_base
        raw_items = _fetch(params)
        for s in raw_items:
            try:
                obj = json.loads(s)
            except Exception:
                obj = {}
            prod = obj.get("product", {})
            attrs = prod.get("attributes", {})
            sku = prod.get("sku")
            region = attrs.get("regionCode")
            all_rows.append({"sku": sku, "regionCode": region, "raw_json": s})

    df_raw = pd.DataFrame(all_rows).drop_duplicates(subset=["sku","raw_json"])

    # Salvar
    if output_format.lower() == "csv":
        df_raw.to_csv(output_path, index=False)
    else:
        df_raw.to_parquet(output_path, index=False)

    print(f"✅ Salvo {len(df_raw)} linhas em: {output_path}")
    return df_raw
