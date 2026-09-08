import json 
import os 
from mtg_findcard import card_search 
from PySide6.QtWidgets import QApplication  
from  Collection_files import Get_Collection
def card_dump(win, Error=False, file_name=None):
    QApplication.processEvents()
    if file_name is None:
        file_name = Get_Collection()
    name = win
    data = card_search(win=name)

    if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
        with open(file_name, "r") as file:
            cards = json.load(file)
    else:
        cards = {}

    cards.update(data)

    with open(file_name, "w") as file:
        json.dump(cards, file, indent=4)

    QApplication.processEvents()
    return True


def card_del(cards, key, file_name=None):
    cards.pop(key)
    if file_name is None:
        file_name = Get_Collection()
    with open(file_name, "w") as file:
        json.dump(cards, file, indent=4)
    return cards