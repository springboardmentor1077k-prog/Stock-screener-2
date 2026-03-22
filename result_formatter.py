def format_results(rows):

    results = []

    for row in rows:
        results.append({
            "company_name": row[0]
        })

    return {
        "status": "success",
        "count": len(results),
        "results": results
    }