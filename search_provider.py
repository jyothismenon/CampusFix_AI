import os
import re
import urllib.request
import urllib.parse
import json

def get_search_credentials():
    # Try Streamlit secrets first
    try:
        import streamlit as st
        provider = st.secrets.get("SEARCH_PROVIDER", "serper")
        api_key = st.secrets.get("SEARCH_API_KEY", None)
        if api_key:
            return provider, api_key
    except Exception:
        pass
    
    # Fallback to environment variables
    provider = os.getenv("SEARCH_PROVIDER", "serper")
    api_key = os.getenv("SEARCH_API_KEY", None)
    return provider, api_key


def parse_price_from_text(text):
    """
    Regex parser for Indian prices:
    Matches: ₹249, ₹ 249, Rs. 249, Rs 249, INR 249, 1,249, 249.00, etc.
    Returns numeric float value in INR or None.
    """
    if not text:
        return None
    
    # Matches patterns like ₹ 1,249.00 or Rs. 249 or 1,249
    patterns = [
        r'(?:₹|Rs\.?|INR)\s*([0-9,]+(?:\.[0-9]{2})?)', # Currency prefix
        r'\b([0-9,]+\.[0-9]{2})\b',                    # Naked decimals
        r'\b([0-9,]{2,10})\b'                          # Naked comma-separated digits (e.g. 1,240)
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            # Clean and parse
            cleaned = m.replace(",", "")
            try:
                val = float(cleaned)
                # Filter out unrealistically low or high prices for standard maintenance items
                if 5.0 <= val <= 250000.0:
                    return val
            except ValueError:
                continue
    return None


def extract_source_from_url(url):
    if not url:
        return "Online Store"
    parsed = urllib.parse.urlparse(url)
    netloc = parsed.netloc.lower()
    # Clean up www.
    if netloc.startswith("www."):
        netloc = netloc[4:]
    # Map common websites to nice names
    mapping = {
        "amazon.in": "Amazon India",
        "flipkart.com": "Flipkart",
        "moglix.com": "Moglix",
        "industrybuying.com": "IndustryBuying",
        "toolsvilla.com": "ToolsVilla",
        "indiamart.com": "IndiaMART",
    }
    for k, v in mapping.items():
        if k in netloc:
            return v
    return netloc.title()


def is_relevant_product(normalized_part, title, snippet):
    """
    Checks if search result is relevant to the normalized part name.
    Splits the part name into key alphanumeric tokens and ensures at least some match.
    """
    tokens = [t.lower() for t in re.findall(r'\b\w+\b', normalized_part) if len(t) > 1]
    # Filter out common units / generic words
    stopwords = {"price", "india", "buy", "online", "spec", "specification", "store"}
    filtered_tokens = [t for t in tokens if t not in stopwords]
    
    if not filtered_tokens:
        return True
        
    combined = (title + " " + snippet).lower()
    # At least 50% of the core query tokens should be present in the title/snippet
    match_count = sum(1 for token in filtered_tokens if token in combined)
    return match_count >= max(1, len(filtered_tokens) // 2)


def search_web_prices(normalized_part):
    """
    Main web price search orchestrator. Returns a list of dicts:
    [{"seller": ..., "price": ..., "availability": ..., "link": ..., "product_name": ...}]
    sorted by price ascending, or raises an Exception.
    """
    provider, api_key = get_search_credentials()
    
    if not api_key:
        raise ValueError("Live price search is not configured. Add SEARCH_API_KEY in Streamlit Secrets.")

    # Formulate multiple query variations to hit different search spaces
    queries = [
        f"{normalized_part} price India site:amazon.in OR site:flipkart.com OR site:moglix.com",
        f"{normalized_part} buy online price India",
        f"{normalized_part} price Amazon India"
    ]
    
    all_raw_results = []
    
    # We query the variations sequentially and merge
    for q in queries[:2]: # Query top 2 variations to be fast & save rate limits
        try:
            results = []
            if provider == "serper":
                results = _query_serper(q, api_key)
            elif provider == "serpapi":
                results = _query_serpapi(q, api_key)
            else:
                # Default to serper if unrecognized provider but key is present
                results = _query_serper(q, api_key)
            
            all_raw_results.extend(results)
        except Exception as e:
            # Log query error internally and try next or raise if final
            print(f"[Search Provider Log] Provider: {provider} | Query: {q} | Error: {e}")
            
    # If we got absolutely nothing, try DDG fallback (not guaranteed)
    if not all_raw_results:
        try:
            all_raw_results = _query_ddg_fallback(queries[0])
        except Exception as e:
            print(f"[Search Provider Log] DDG Fallback Error: {e}")

    # Process and extract products
    extracted_products = []
    parsing_failures = 0
    
    for item in all_raw_results:
        title = item.get("title", "")
        link = item.get("link", "")
        snippet = item.get("snippet", "")
        
        # Check relevance
        if not is_relevant_product(normalized_part, title, snippet):
            continue
            
        # Parse price from title or snippet
        price = parse_price_from_text(title)
        if price is None:
            price = parse_price_from_text(snippet)
            
        if price is None:
            parsing_failures += 1
            continue
            
        seller = extract_source_from_url(link)
        
        extracted_products.append({
            "product_name": title[:80] + "..." if len(title) > 80 else title,
            "seller": seller,
            "price": price,
            "availability": "In Stock",
            "link": link
        })

    # Log search telemetry
    print(f"[Search Provider Log] Provider: {provider} | Query: {normalized_part} | Results count: {len(all_raw_results)} | Parsing failures: {parsing_failures}")

    if not extracted_products:
        return []

    # Sort results by price ascending
    return sorted(extracted_products, key=lambda x: x["price"])


def _query_serper(query, api_key):
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    data = json.dumps({"q": query, "gl": "in", "hl": "en"}).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=10) as response:
        res_body = response.read().decode("utf-8")
        data = json.loads(res_body)
        organic = data.get("organic", [])
        return [{"title": o.get("title"), "link": o.get("link"), "snippet": o.get("snippet")} for o in organic]


def _query_serpapi(query, api_key):
    params = urllib.parse.urlencode({
        "q": query,
        "api_key": api_key,
        "engine": "google",
        "gl": "in",
        "hl": "en"
    })
    url = f"https://serpapi.com/search.json?{params}"
    
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=10) as response:
        res_body = response.read().decode("utf-8")
        data = json.loads(res_body)
        organic = data.get("organic_results", [])
        return [{"title": o.get("title"), "link": o.get("link"), "snippet": o.get("snippet")} for o in organic]


def _query_ddg_fallback(query):
    params = urllib.parse.urlencode({"q": query})
    url = f"https://html.duckduckgo.com/html/?{params}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=10) as response:
        html = response.read().decode("utf-8")
        links = re.findall(r'<a class="result__url"[^>]*href="([^"]+)"', html)
        titles = re.findall(r'<a class="result__snippet"[^>]*>([^<]+)</a>', html)
        results = []
        for idx in range(min(len(links), len(titles))):
            results.append({
                "title": titles[idx].strip(),
                "link": urllib.parse.unquote(links[idx]),
                "snippet": titles[idx].strip()
            })
        return results
