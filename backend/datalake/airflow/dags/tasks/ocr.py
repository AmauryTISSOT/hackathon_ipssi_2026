from datetime import datetime


def extract_ocr(**context):
    from minio import Minio
    import easyocr
    from pdf2image import convert_from_bytes
    import json, os, io
    import numpy as np
    from PIL import Image

    client = Minio(
        os.environ["MINIO_ENDPOINT"],
        access_key=os.environ["MINIO_ACCESS_KEY"],
        secret_key=os.environ["MINIO_SECRET_KEY"],
        secure=False,
    )

    doc_name = context["ti"].xcom_pull(task_ids="store_bronze")
    response = client.get_object("bronze", doc_name)
    file_bytes = response.read()
    response.close()
    response.release_conn()

    reader = easyocr.Reader(["fr"], gpu=True)

    if doc_name.lower().endswith(".pdf"):
        images = convert_from_bytes(file_bytes, dpi=150)
        all_results = []
        for page_num, image in enumerate(images):
            img_array = np.array(image)
            results = reader.readtext(img_array, batch_size=8)
            all_results.append({
                "page": page_num + 1,
                "blocks": [
                    {"text": text, "confidence": float(conf)}
                    for (bbox, text, conf) in results
                ],
            })
    else:
        image = Image.open(io.BytesIO(file_bytes))
        img_array = np.array(image)
        results = reader.readtext(img_array, batch_size=8)
        all_results = [{
            "page": 1,
            "blocks": [
                {"text": text, "confidence": float(conf)}
                for (bbox, text, conf) in results
            ],
        }]

    full_text = "\n".join(
        block["text"] for page in all_results for block in page["blocks"]
    )
    silver_data = {
        "source_file": f"bronze/{doc_name}",
        "extracted_text": full_text,
        "pages": len(all_results),
        "details": all_results,
        "ocr_engine": "easyocr",
        "processed_at": datetime.utcnow().isoformat() + "Z",
    }

    silver_key = "silver_" + doc_name.rsplit(".", 1)[0] + ".json"
    json_bytes = json.dumps(silver_data, ensure_ascii=False).encode("utf-8")
    client.put_object(
        "silver", silver_key, io.BytesIO(json_bytes), len(json_bytes),
        content_type="application/json",
    )

    print(f"[OCR] {len(all_results)} page(s), {len(full_text)} chars → silver/{silver_key}")
    return full_text
