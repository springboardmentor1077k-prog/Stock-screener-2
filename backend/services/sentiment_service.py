import requests

NEWS_API = "https://newsapi.org/v2/everything"


def get_market_news(company):

    params = {
        "q": company,
        "sortBy": "publishedAt",
        "apiKey": "YOUR_API_KEY"
    }

    response = requests.get(NEWS_API, params=params)

    data = response.json()

    articles = data.get("articles", [])

    return [
        {
            "title": a["title"],
            "url": a["url"],
            "source": a["source"]["name"]
        }
        for a in articles[:5]
    ]