import requests

url = 'https://api.scryfall.com/cards/autocomplete'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}
def autocomplete(card_name):
    params = {
        "q": card_name 
    }
    response = requests.get(url, headers=headers, params=params)
    re_dict = response.json()
    cards_list = re_dict.get('data', [])
    cards_list = cards_list[:75]
    print(f"Status Code: {response.status_code}")
    return cards_list
if __name__ == "__main__":
    print(autocomplete(input("cardname: ")))