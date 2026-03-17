def store_bronze(**context):
    doc_name = context["dag_run"].conf.get("doc_name", "facture_example.pdf")
    print(f"[BRONZE] Document '{doc_name}' prêt dans le bucket bronze.")
    return doc_name
