import requests,csv
import mtg_autocomplete
import sys
import platform

url = 'https://api.scryfall.com/cards/collection'

def build_user_agent():
    system = platform.system()
    if system == "Windows":
        os_string = "Windows NT 10.0; Win64; x64"
    elif system == "Darwin":
        os_string = "Macintosh; Intel Mac OS X 10_15_7"
    elif system == "Linux":
        os_string = "X11; Linux x86_64"
    else:
        os_string = "Windows NT 10.0; Win64; x64"  # fallback

    return f"Mozilla/5.0 ({os_string}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

headers = {
    'User-Agent': build_user_agent(),
    'Accept': 'application/json'
}
batch_size = 75

payload = {
"identifiers": [
]
}
def card_search(win):
    cards = []
    cards_list = []
    card_names = []
    try:
        with open(win, mode='r') as file:
            for line in file:
                line = line.lstrip("1 ")
                line = line.rstrip("\n")
                if line != "":
                    cards.append(line)
        if cards[0] == "clear":
            return "clear"
        cards_list = []
        print(len(cards))
        card_batches = [cards[i : i + batch_size] for i in range(0, len(cards), batch_size)]
        for index, batch in enumerate(card_batches):
            for i in batch:
                payload['identifiers'].append({ "name": i})
            response = requests.post(url, headers=headers, json=payload)
            re_dict = response.json()
            cards_list.append(re_dict.get('data', []))
            payload['identifiers'] = []

        print(f"Status Code: {response.status_code}")
        if cards_list == []:
            print("no cards found")
        o = 0
        card_data = {}
        card_data = dict(card_data)
        for i in cards_list:
                print(f"i:{len(i)}")
                for l in i:
                    o = o+1
                    card_data[l["name"]] = l
        return card_data
    except:
        return {}