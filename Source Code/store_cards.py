import json 
import os 
from mtg_findcard import card_search 
from PySide6.QtWidgets import QApplication  
from  Collection_files import Get_Collection

def card_dump( win, Error=False):
    QApplication.processEvents()

    data = card_search(win=win)
    file_name = Get_Collection()

    if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
        with open(file_name, "r") as file:
            cards = json.load(file)
    else:
        cards = {}
    l = cards
    if l == cards:
        print("err")
    if cards != "clear" and cards != "clear " and cards != " clear" and cards != "Clear": 
            cards.update(data)
    print("Updated collection:", cards)
    if cards == "clear" or cards == "clear " or cards == " clear" or cards == "Clear":
        cards = {}
    with open(file_name, "w") as file:
        json.dump(cards, file, indent=4)
        
    QApplication.processEvents()
    
    return True
def card_del(cards,key):
    cards.pop(key)
    file_name = Get_Collection()
    with open(file_name,"w") as file:
        json.dump(cards,file,indent=4)
    return cards
