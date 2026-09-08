from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QWidget, QHBoxLayout, QPushButton,QFileDialog,QMessageBox,QVBoxLayout,
QScrollArea,QGridLayout,QLineEdit,QComboBox,QMenu,QListView)
from PySide6.QtGui import QIcon,QPixmap,QMouseEvent,QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt,QSize,QTimer
from store_cards import card_dump,card_del
from PySide6.QtCore import Qt, QThread, Signal,QPropertyAnimation, QEasingCurve,QUrl,QEvent,QObject
import time,json,os
import requests
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply 
import re
from Collection_files import Get_Collection,Set_Collection
app = QApplication.instance()
if not app:
    app = QApplication([])
import webbrowser 
from shiboken6 import isValid
import difflib

if len(os.listdir("Collections")) < 1:
    if os.path.exists("config.json") and os.path.getsize("config.json") > 0:
        Set_Collection("Collection")
    else:
        with open("config.json","w") as file:
            json.dump({"File Name":"Collection"}, file, indent=4)
        Set_Collection("Collection")
class Worker(QObject):
    finished = Signal()
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, file_path, target_file=None):
        super().__init__()
        self.file_path = file_path
        self.target_file = target_file

    def run(self):
        try:
            if self.target_file:
                card_dump(win=self.file_path, Error=False, file_name=self.target_file)
            else:
                card_dump(win=self.file_path, Error=False)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()
class MainWindow(QMainWindow): 
    def __init__(self): 
        super().__init__() 
        self.setWindowTitle("Menu")
        self.setWindowIcon(QIcon("images\\Window_icon_circle.png"))
        self.resize(350,150)
        self.setFixedSize(350,150)
        self.main_layout = QVBoxLayout()
        container = QWidget() 
        upload_button = QPushButton("Upload Cards")
        quit_button = QPushButton("Quit")
        setting_button = QPushButton("Settings")
        collection_button = QPushButton("Collection")  
        setting_button.clicked.connect(self.show_settings)
        upload_button.clicked.connect(self.file_search)
        collection_button.clicked.connect(self.show_collection)

        self.main_layout.addWidget(upload_button)
        self.main_layout.addWidget(collection_button)
        self.main_layout.addWidget(setting_button)
        self.main_layout.addWidget(quit_button)
        self.main_layout.addStretch(1)


        quit_button.clicked.connect(self.close) 
        self.main_layout.addWidget(collection_button)


        container.setLayout(self.main_layout) 
        self.setCentralWidget(container) 

    def file_search(self, *_): 
        file_path, _ = QFileDialog.getOpenFileName( 
                None, 
                "Select a file", 
                "", 
                "Text Files (*.txt)" 
            ) 
        if file_path != "":
            self.msgBox = QMessageBox(self)
            self.msgBox.setWindowTitle("Download")
            self.msgBox.setText("<div style='text-align: center;'>Downloading...</div>")
            self.msgBox.setInformativeText("<div style='text-align: Bottom;'><font size='2'>This will only take a few seconds.</font></div>")

            self.msgBox.setStandardButtons(QMessageBox.StandardButton.NoButton)

            self.msgBox.show()
            self.thread = QThread()
            self.worker = Worker(file_path)
            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.on_download_finished)
            self.worker.error.connect(self.on_download_error)

            # cleanup
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)

            self.thread.start()
    def on_download_finished(self):
        self.msgBox.setText("<div style='text-align: center;'>Download finished</div>")
        self.msgBox.setInformativeText("")
        self.msgBox.setStandardButtons(QMessageBox.StandardButton.Ok)

    def on_download_error(self, message):
        self.msgBox.close()
        QMessageBox.warning(self, "Download failed", message)
            
    def show_settings(self):
        self.settings_window = Settings()
    def show_collection(self):
        self.collection_window = Collection(on_final_close=self.fade_in_main)

        self.collection_window.closed_signal.connect(self.fade_in_main,)


        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(250)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self.anim.finished.connect(self.open_collection_finished)
        self.anim.start()
    def open_collection_finished(self):
        self.hide()
        self.setWindowOpacity(1.0) 
        
        self.collection_window.setWindowOpacity(0.0)
        self.collection_window.show()
        
        self.collection_anim = QPropertyAnimation(self.collection_window, b"windowOpacity")
        self.collection_anim.setDuration(250)
        self.collection_anim.setStartValue(0.0)
        self.collection_anim.setEndValue(1.0)
        self.collection_anim.setEasingCurve(QEasingCurve.InCubic)
        self.collection_anim.start()
    def fade_in_main(self):
        self.setWindowOpacity(0.0)
        self.show()
        
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(250)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.InCubic)
        self.anim.start()
class MoveBus(QObject):
    moved = Signal(str)  # emits target collection name

move_bus = MoveBus()
class Settings(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("images/Cog_wheel_icon.png"))
        self.setWindowTitle("Settings")
        self.main_layout = QVBoxLayout(self)  
        self.Collection_name = QLabel("")
        self.Collection_label = QLabel("Collection Name:")
        self.name = QLineEdit(placeholderText=str(Get_Collection().removesuffix(".json").replace("Collections","")).replace("\\",""))
        self.confirm_button = QPushButton("Add")

        #self.del_label = QLabel("   ")
        #self.del_name = QLineEdit(placeholderText="File Name")
        self.del_button = QPushButton("Delete")



        self.confirm_button.clicked.connect(self.change_Collection)
        self.del_button.clicked.connect(self.DelateFile)
        self.another_layout = QHBoxLayout(self)
        self.another_layout.addWidget(self.Collection_label)
        self.another_layout.addWidget(self.name)
        #self.another_layout.addWidget(self.confirm_button)
        #self.main_layout.addWidget(self.Collection_name)
        self.main_layout.addLayout(self.another_layout)
        self.three_layout = QHBoxLayout(self)
        self.three_layout.addWidget(self.confirm_button)
        self.three_layout.addWidget(self.del_button)
        self.main_layout.addLayout(self.three_layout)
    
        self.show()
    def change_Collection(self):
        if self.name.text().strip() != "":
            Set_Collection(text=self.name.text())
            self.close()
            self.settings_window = Settings()
    def DelateFile(self):
        if len(os.listdir("Collections")) > 1:
            text = self.name.text()
            if self.name.text().strip() == "":
                text = self.name.placeholderText()
            try:
                os.remove("Collections\\"+text+".json")
            except FileNotFoundError:
                print("File doesn't exist, nothing to delete")
        self.close()
        self.settings_window = Settings()
class Add_collection_pop_up(QWidget):
    added_collection = Signal(str)
    def __init__(self):
        super().__init__()
        window_layout = QVBoxLayout(self)
        self.setWindowTitle("Collection Editor")
        self.closed = False
        self.setWindowIcon(QIcon("images\\Cog_wheel_icon.png"))
        self.setFixedSize(QSize(300,100))
        window_layout_enter = QHBoxLayout()
        self.info = QLabel("Collection Name:")
        self.add_collection_textline = QLineEdit(placeholderText="Collection")
        self.confirm_button = QPushButton("Add Collection")
        self.confirm_button.clicked.connect(self.Add_New_Collection)
        window_layout_enter.addWidget(self.info)
        window_layout_enter.addWidget(self.add_collection_textline)
        window_layout.addLayout(window_layout_enter)
        window_layout.addWidget(self.confirm_button)


        self.show()
    def Add_New_Collection(self):
        if self.add_collection_textline.text().strip() != "":
                    Set_Collection(text=self.add_collection_textline.text())
                    self.closed = True
                    self.new_collection = self.add_collection_textline.text()
                    self.added_collection.emit(self.new_collection)   # notify listeners
                    self.close()
class Rename_collection_pop_up(QWidget):
    renamed = Signal(str, str)  # old_name, new_name
    def __init__(self,name):
        super().__init__()
        window_layout = QVBoxLayout(self)
        self.setWindowTitle("Collection Editor")
        self.name = name
        self.closed = False
        self.setWindowIcon(QIcon("images\\Cog_wheel_icon.png"))
        self.setFixedSize(QSize(300,100))
        window_layout_enter = QHBoxLayout()
        self.info = QLabel("Collection Name:")
        self.add_collection_textline = QLineEdit(placeholderText="Collection",text=name)
        self.confirm_button = QPushButton("Rename Collection")
        self.confirm_button.clicked.connect(self.Add_New_Collection)
        window_layout_enter.addWidget(self.info)
        window_layout_enter.addWidget(self.add_collection_textline)
        window_layout.addLayout(window_layout_enter)
        window_layout.addWidget(self.confirm_button)

        self.show()

    def Add_New_Collection(self):
        new_name = self.add_collection_textline.text().strip()
        if new_name == "" or new_name == self.name:
            self.close()
            return

        old_path = os.path.join("Collections", f"{self.name}.json")
        new_path = os.path.join("Collections", f"{new_name}.json")

        if os.path.exists(new_path):
            QMessageBox.warning(self, "Rename failed",
                                 f"A collection named '{new_name}' already exists.")
            return

        try:
            os.rename(old_path, new_path)
        except OSError as e:
            QMessageBox.warning(self, "Rename failed", str(e))
            return

        self.closed = True
        self.renamed.emit(self.name, new_name)
        self.close()
class LeftClickOnlyListView(QListView):
    def __init__(self, combo_box=None):
        super().__init__()
        self.combo_box = combo_box

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            if self.combo_box is not None:
                self.combo_box._suppress_next_hide = True
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            if self.combo_box is not None:
                self.combo_box._suppress_next_hide = True
            return
        super().mouseReleaseEvent(event)
class RightClickSafeComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._suppress_next_hide = False

    def hidePopup(self):
        if self._suppress_next_hide:
            self._suppress_next_hide = False
            return   # veto the close entirely
        super().hidePopup()

class Collection(QWidget):

    closed_signal = Signal()
    Additional_closed_signal = Signal(str)
    Moved_to_signal = Signal(str)
    def __init__(self,on_final_close=None,additional_window=False):
        super().__init__()
        move_bus.moved.connect(self._on_card_moved_here)
        self.card_objs = []
        self.disabled = []
        self.windows = []
        self.additional_window = additional_window
        self.on_final_close = on_final_close
        self.true_close = True
        self.sort_key = "name"
        self.sort_reverse = True
        self.last_click_time = 0
        self.debounce_ms = 300
        self.download_queue = []    
        self._downloading = False
        container_widget = QWidget()
        self.setWindowTitle("Collection")
        self.setWindowIcon(QIcon("images\\Window_icon_circle.png"))
        self.resize(750,750/1.25)
        self.setMaximumSize(750,750)

        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(250)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)


        self.btnbox = QGridLayout(container_widget)
        window_layout = QVBoxLayout(self)
        window_h_layout = QHBoxLayout()

        self.collection_combo_box = RightClickSafeComboBox()
        self.collection_combo_box.setView(LeftClickOnlyListView(combo_box=self.collection_combo_box))
        for filename in os.listdir("Collections"):
            if filename.endswith(".json"):
                name = filename.removesuffix(".json")
                self.collection_combo_box.addItem(name)
        self.collection_combo_box.installEventFilter(self)
        self.collection_combo_box.view().viewport().installEventFilter(self)
        if not additional_window:
            current_name = os.path.splitext(os.path.basename(Get_Collection()))[0]
            load_path = Get_Collection()
        else:
            self.setWindowTitle(f"Collection:{additional_window}")
            current_name = additional_window
            load_path = f"Collections\\{additional_window}.json"
            self.collection_combo_box.setEnabled(False)
        index = self.collection_combo_box.findText(current_name)
        if index != -1:
            self.collection_combo_box.setCurrentIndex(index)
        self.scroll = QScrollArea(self) 
        self.scroll.setWidgetResizable(True)





        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(200)  
        self._search_timer.timeout.connect(self._do_rebuild)
        self.collection_combo_box.currentTextChanged.connect(self.change_collection)

        self.searchbar = QLineEdit(placeholderText="Enter Text")
        self.searchbar.textChanged.connect(self.update_display)

        self.sort = QComboBox(editable=False)
        self.sort.addItems(["Name", "Mana Value", "Power","Toughness","Price"])
        self.sort.currentTextChanged.connect(self.filter_change)

        self.sort_dir = QPushButton()
        self.sort_dir.setIcon(QIcon("images/down_arrow_rounded.png"))
        self.sort_dir.clicked.connect(self.filter_dir)
        self.sort_dir.setFixedSize(QSize(25,25))
        self.sort_dir.setIconSize(self.sort_dir.size())
        self.btnbox.setSpacing(15)
        self.network_manager = QNetworkAccessManager(self)


        self.cards = {} 
        with open(load_path,'r') as file:
            self.cards = json.load(file)

        self.card_widgets = {}
        
        for index, key in enumerate(sorted(self.cards.keys(),key=self.get_sort_func_by_name(),reverse=self.sort_reverse)):
            row = index // 4
            col = index % 4
            card_widget = QWidget()
            card_widget.setFixedSize(140, 180)

            card_layout = QVBoxLayout(card_widget)
            card_layout.setContentsMargins(5, 5, 5, 5)
            card_layout.setSpacing(5)



            img_label = QLabel()
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_label.setStyleSheet("border: 1px solid #ccc; border-radius: 4px; background-color: #f0f0f0;")
            

            text_label = QLabel(key)
            text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            text_label.setWordWrap(True)
            text_label.setStyleSheet("font-size: 10px; font-weight: bold; color: #F2F3F5;")

            card_layout.addWidget(img_label)
            card_layout.addWidget(text_label)

            card_widget.setStyleSheet("""
                QWidget:hover { background-color: #353839; border-radius: 6px; }
            """)

            card_widget.installEventFilter(self)

            self.btnbox.addWidget(card_widget,row,col) 

            self.card_widgets[key] = card_widget

            card_data = self.cards[key]
            self.card_objs.append(card_widget)
            card_widget.custom_data = {"key":key,"card_data":card_data,"img label":img_label,"card face":0,"downloaded":False}
            FALLBACK_URL = "https://cards.scryfall.io/normal/front/2/9/294e0651-99b4-4792-8ee8-107e7484117d.jpg?1786005602"

            image_dict = card_data.get('image_uris')
            if not image_dict:
                print(f"No image_uris for {key}, falling back to placeholder")
            if not image_dict and 'card_faces' in card_data:
                image_dict = card_data['card_faces'][0].get('image_uris')
            img_url = (image_dict or {}).get('normal') or FALLBACK_URL
            self.download_queue.append((img_url, img_label, card_widget))

        self.rebuild_grid()
        window_layout.addWidget(self.collection_combo_box)
        window_h_layout.addWidget(self.searchbar)
        window_h_layout.addWidget(self.sort)
        window_h_layout.addWidget(self.sort_dir)
        window_layout.addLayout(window_h_layout) 


        self.scroll.setWidget(container_widget)
        window_layout.addWidget(self.scroll)
        self._start_next_download()
    def clear_scroll_area(self):
        layout = self.scroll.widget().layout()
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
    def _on_collection_renamed(self, old_name, new_name):
        index = self.collection_combo_box.findText(old_name)
        if index == -1:
            return
        is_current = (index == self.collection_combo_box.currentIndex())
        if is_current:
            Set_Collection(new_name)
            if self.additional_window:
                self.additional_window = new_name
                self.setWindowTitle(f"Collection:{new_name}")
        # update the displayed name without re-triggering a reload,
        # since the underlying file's contents haven't changed
        self.collection_combo_box.blockSignals(True)
        self.collection_combo_box.setItemText(index, new_name)
        self.collection_combo_box.blockSignals(False)
    def change_collection(self):
        if not self.additional_window:
            Set_Collection(self.collection_combo_box.currentText())
            self.stop_downloads()
            self.clear_scroll_area()
            self.cards = {} 
            with open(Get_Collection(),'r') as file:
                self.cards = json.load(file)

            self.card_widgets = {}
            
            for index, key in enumerate(sorted(self.cards.keys(),key=self.get_sort_func_by_name(),reverse=self.sort_reverse)):
                row = index // 4
                col = index % 4
                card_widget = QWidget()
                card_widget.setFixedSize(140, 180)

                card_layout = QVBoxLayout(card_widget)
                card_layout.setContentsMargins(5, 5, 5, 5)
                card_layout.setSpacing(5)



                img_label = QLabel()
                img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                img_label.setStyleSheet("border: 1px solid #ccc; border-radius: 4px; background-color: #f0f0f0;")
                

                text_label = QLabel(key)
                text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                text_label.setWordWrap(True)
                text_label.setStyleSheet("font-size: 10px; font-weight: bold; color: #F2F3F5;")

                card_layout.addWidget(img_label)
                card_layout.addWidget(text_label)

                card_widget.setStyleSheet("""
                    QWidget:hover { background-color: #353839; border-radius: 6px; }
                """)

                card_widget.installEventFilter(self)

                self.btnbox.addWidget(card_widget,row,col) 

                self.card_widgets[key] = card_widget

                card_data = self.cards[key]
                self.card_objs.append(card_widget)
                card_widget.custom_data = {"key":key,"card_data":card_data}
                FALLBACK_URL = "https://cards.scryfall.io/normal/front/2/9/294e0651-99b4-4792-8ee8-107e7484117d.jpg?1786005602"

                image_dict = card_data.get('image_uris')
                if not image_dict:
                    print(f"No image_uris for {key}, falling back to placeholder")
                if not image_dict and 'card_faces' in card_data:
                    image_dict = card_data['card_faces'][0].get('image_uris')
                img_url = (image_dict or {}).get('normal') or FALLBACK_URL
                self.download_queue.append((img_url, img_label, card_widget))

            self.rebuild_grid()
            self._start_next_download()
    def _on_card_moved_here(self,text):
            print(text,"=",self.additional_window)
            if self.additional_window == text:
                print("yes")
                self.Refresh()
            elif self.additional_window == None:
                if Get_Collection().replace("Collections\\","").replace(".json",""):
                    print("yes")
                    self.Refresh()
    def on_download_finished(self):
            self.msgBox.setText("<div style='text-align: center;'>Download finished</div>")
            self.msgBox.setInformativeText("")
            self.msgBox.setStandardButtons(QMessageBox.StandardButton.Ok)
    
    def on_download_error(self, message):
        self.msgBox.close()
        QMessageBox.warning(self, "Download failed", message)
    def filter_dir(self):
        self.sort_reverse = not self.sort_reverse
        if self.sort_reverse == True:
            self.sort_dir.setIcon(QIcon("images/down_arrow_rounded.png"))
        else:
            self.sort_dir.setIcon(QIcon("images/up_arrow_rounded.png"))
        self.update_display(None)
    def _start_next_download(self):
        if self._downloading:
            return
        if not self.download_queue:
            return
        self._downloading = True
        url, label, card_widget = self.download_queue.pop(0)
        request = QNetworkRequest(QUrl(url))
        reply = self.network_manager.get(request)
        self._current_reply = reply
        reply.finished.connect(
            lambda r=reply, l=label, c=card_widget: self.on_image_downloaded(r, l, c)
        )
    def stop_downloads(self):
        self.download_queue.clear()
        
        try:
            if self._current_reply is not None and isValid(self._current_reply):
                self._current_reply.abort()
        except Exception as e:
                    print(f"[stop_downloads] {type(e).__name__}: {e}")
        self._current_reply = None
        self._current_reply = None
    def update_display(self,text=None):
        try:
            search = text.strip().casefold()
            self._pending_search_text = text
            self._search_timer.start()
        except:
            text=self.searchbar.text()
            search = text.strip().casefold()
            self._pending_search_text = text
            self._search_timer.start()
    def _do_rebuild(self):
        self.rebuild_grid(self._pending_search_text)
    def filter_change(self,text):
            if text == "Name":
                self.sort_reverse =  self.sort_reverse
                self.sort_key = "name"
            elif text == "Mana Value":
                self.sort_key = "cmc"
            elif text == "Power":
                self.sort_key = "power"
            elif text == "Toughness":
                self.sort_key = "toughness"
            elif text == "Price":
                self.sort_key = "price"
            print(text,self.sort_key)
            self.update_display(None)
    def rebuild_grid(self,filter=""):
        oracle_search = False
        while self.btnbox.count():
            item = self.btnbox.takeAt(0)
        visible_count = 0
        search_term = filter.strip().lower()
        TAGS = r'legal:|!legal:|o:|t:|gc:|!o:|!t:|m:|!m:|m=:|!m=:|pow(?:<=|>=|<|>|=):|tou(?:<=|>=|<|>|=):|cmc(?:<=|>=|<|>|=):|usd(?:<=|>=|<|>|=):'
        tag_pattern = rf'(?:^|(?<=\s))({TAGS})\s*(.*?)(?=\s*(?:{TAGS})|$)'
        matches = re.findall(tag_pattern, filter)
        print(repr(tag_pattern))
        print(re.compile(tag_pattern).groups) 
        print(matches[:5])
        search_tags = [{tag[:-1]:val.strip()} for tag, val in matches if val.strip()]
        base_name_search = re.sub(tag_pattern, '', filter).strip().lower()
        print(search_tags)
        print("tags:", search_tags)
        print("base_name_search:", repr(base_name_search))
        keyfunc = self.get_sort_func_by_name()
        for i, (name, widget) in enumerate(sorted(self.card_widgets.items(),reverse=self.sort_reverse,key=lambda kv:keyfunc(kv[0]))):
            is_card = True
            card_data = self.cards[name]
            card_oracle_text = card_data.get("oracle_text", "").lower()
            card_type_text = card_data.get("type_line", "").lower()
            mana = card_data.get("mana_cost")
            legal = True
            format = ['standard', 'future', 'historic', 'timeless', 'gladiator', 'pioneer', 'modern', 'legacy', 'pauper', 'vintage', 'penny', 'commander', 'oathbreaker', 'standardbrawl', 'brawl', 'competitivebrawl', 'alchemy', 'paupercommander', 'duel', 'oldschool', 'premodern', 'predh', 'tlr']
            game_changer_status = str(card_data.get("game_changer")).lower()
            try:
                power = (card_data["power"]).strip()
                toughness = card_data["toughness"].strip()
            except:
                power = 0
                toughness = 0
            if power == "*":
                power = 0
            if toughness == "*":
                toughness = 0
            if not search_tags:

                if search_term not in name.lower():
                    is_card = False

            else:
                for card_dict in search_tags:
                    
                    key = next(iter(card_dict))
                    val = card_dict[key]
                    val = val.lower()
                    if "legal" in key:
                        try:
                            matches = difflib.get_close_matches(val,format,  n=1, cutoff=0.6)
                            legal = card_data.get("legalities")[matches[0]]
                        except:
                            print("not yet")
                    if key == "o" and val not in card_oracle_text:
                        is_card = False
                    elif key == "!o" and val in card_oracle_text:
                        is_card = False
                    elif key == "t" and val not in card_type_text:
                        is_card = False
                    elif key == "!t" and val in card_type_text:
                        is_card = False
                    elif key == "m" and val.lstrip("{").rstrip("}") not in mana.lstrip("{").rstrip("}").lower():
                        is_card = False
                    elif key == "!m" and val.lstrip("{").rstrip("}")  in mana.lstrip("{").rstrip("}").lower():
                            is_card = False
                    elif key == "legal" and legal != "legal":
                        print(key,"not legal")
                        
                        is_card = False
                    
                    elif key =="!legal" and  legal != "not_legal" and legal != "banned":
                        is_card = False
                    elif key.startswith(("pow", "tou","cmc","usd")):
                        try:
                            stat_type = "power" if key.startswith("pow") else ("toughness" if key.startswith("tou") else ("cmc" if key.startswith("cmc") else "prices"))
                            card_stat_raw = card_data.get(stat_type)
                            if stat_type == "prices":
                                card_stat_raw = card_stat_raw.get("usd") if card_stat_raw else None
                            target_val = float(val)
                            card_stat_val = float(card_stat_raw)

                            op = key[3:] 

                            if op == ">=":
                                passed = card_stat_val >= target_val
                            elif op == "<=":
                                passed = card_stat_val <= target_val
                            elif op == ">":
                                passed = card_stat_val > target_val
                            elif op == "<":
                                passed = card_stat_val < target_val
                            elif op == "=":
                                passed = card_stat_val == target_val
                            else:
                                passed = True  

                            if not passed:
                                is_card = False
                        except Exception:
                            is_card = False
                    elif key == "gc" and val != game_changer_status:
                        is_card = False
                if base_name_search not in name.lower():
                    is_card = False
                

            if is_card:
                widget.show()
                row = visible_count // 4
                col = visible_count % 4
                self.btnbox.addWidget(widget, row, col)
                visible_count += 1
            else:
                widget.hide()
        
    def on_image_downloaded(self, reply, label,card_widget):
        try:
            if not isValid(reply):
                return

            if reply.error() == QNetworkReply.NetworkError.NoError:
                data = reply.readAll()
                if data:
                    pixmap = QPixmap()
                    pixmap.loadFromData(data)

                    if not pixmap.loadFromData(data):
                        print(f"Failed to decode image data (size={data.size()}) from {reply.url().toString()}")
                        if isValid(label):
                            label.setText("No image")
                            return

                    print(f"{reply.url().toString()} -> {pixmap.width()}x{pixmap.height()}, isNull={pixmap.isNull()}")
                    ratio = self.devicePixelRatio()
                    target_w = int(120 * ratio)
                    target_h = int(150 * ratio)
                    scaled_pixmap = pixmap.scaled(
                        target_w, target_h,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    scaled_pixmap.setDevicePixelRatio(ratio)

                    if isValid(label):
                        label.setPixmap(scaled_pixmap)
                        logical_size = QSize(
                            int(scaled_pixmap.width() / ratio),
                            int(scaled_pixmap.height() / ratio)
                        )
                        label.setFixedSize(logical_size)
                    if isValid(card_widget):
                        margins = card_widget.layout().contentsMargins()
                        spacing = card_widget.layout().spacing()
                        text_label = card_widget.layout().itemAt(1).widget()

                        if isValid(text_label):
                            text_label.setFixedWidth(logical_size.width())
                            text_height = text_label.heightForWidth(logical_size.width())
                            if text_height <= 0:  
                                text_height = text_label.sizeHint().height()
                        else:
                            text_height = 0

                        new_w = logical_size.width() + margins.left() + margins.right()
                        new_h = logical_size.height() + text_height + spacing + margins.top() + margins.bottom()
                        card_widget.setFixedSize(new_w, new_h)
                    else:
                        self.stop_downloads()
            else:
                print(f"Network error: {reply.errorString()}")
                if isValid(label):
                    label.setText("Error loading")
        finally:
            if isValid(reply):
                    reply.deleteLater()
            if isValid(card_widget):
                custom = getattr(card_widget, "custom_data", None)
                if custom is not None:
                    custom["downloaded"] = True

            self._downloading = False
            self._start_next_download()

    def Value(self,event,key):
        if QMouseEvent.button() == Qt.MouseButton.LeftButton:
            print(self.cards[key]["scryfall_uri"])
            webbrowser.open(self.cards[key]["scryfall_uri"])
        print(event.button())

    def get_sort_func_by_name(self):
        if self.sort_key == "power":
            return lambda k: self._safe_stat(self.cards[k].get("power"))
        elif self.sort_key == "toughness":
            return lambda k: self._safe_stat(self.cards[k].get("toughness"))
        elif self.sort_key == "cmc":
            return lambda k: self._safe_stat(self.cards[k].get("cmc"))
        elif self.sort_key == "price":
            return lambda k: self._safe_stat(self.cards[k].get("prices")["usd"])
        else:
            return lambda k: k.lower()

    def _safe_stat(self, val):
        if val is None:
            return 0.0
        val = str(val).strip()
        if val == "*":
            return 0.0
        try:
            return float(val)
        except ValueError:
            return 0.0

    def closeEvent(self, event):
        event.ignore()
        self.stop_downloads()
        try:
            for i in self.windows:
                i.close()
        except Exception as e:
            print(e)
        self.fade_out_and_close()
    def _on_card_moved(self,target_name):
        my_collection_name = self.additional_window if self.additional_window else os.path.splitext(os.path.basename(Get_Collection()))[0]
        if target_name != my_collection_name:
            return
        self.Refresh()
    def _on_additional_window_closed(self,name):
        index = self.collection_combo_box.findText(name)
        model = self.collection_combo_box.model()
        self.disabled.pop(self.disabled.index(name))
        item = model.item(index)
        item.setEnabled(True)
    def drop_down_Add_box_item(self,text,pos):
        if not text in self.disabled:
            menu = QMenu()
            Open_action = menu.addAction("Open")
            Upload_action = menu.addAction("Import")
            action_Export = menu.addAction("Export")
            action_Rename = menu.addAction("Rename")
            Clear_action = menu.addAction("Clear")
            Delete_action = menu.addAction("Delete")
            action = menu.exec(pos)

            if action == Clear_action:
                with open(f"Collections\\{text}.json","w") as file:
                    json.dump({}, file, indent=4)
            elif action == action_Rename:
                 self.popup = Rename_collection_pop_up(text)
                 self.popup.renamed.connect(self._on_collection_renamed)
            elif action == action_Export:
                            exported = ""
                            with open(f"Collections\\{text}.json","r") as file:
                                dict_cards = json.load(file)
                                for key,val in dict_cards.items():
                                    exported = exported+"1 "+key+"\n"
                                folder_path,_ = QFileDialog.getSaveFileName( 
                                                                            None, 
                                                                            "Select a folder", 
                                                                            "", 
                                                                            "txt Files (*.txt)"
                                )
                                print(f"exported to {folder_path}/exported")
                            data = f"{folder_path}/{self._current_file_path().replace("Collections\\","").replace(".json","")} collection export"
                            if folder_path != "":
                                with open(folder_path,"w") as file:
                                    file.write(exported)
            elif action == Open_action:
                len_window = len(self.windows)
                model = self.collection_combo_box.model()
                item = model.item(self.collection_combo_box.findText(text))
                item.setEnabled(False)
                self.disabled.append(text)
                self.windows.append(AdditionalCollection(on_final_close=False,additional_window=text))
                
                self.windows[len_window].Additional_closed_signal.connect(self._on_additional_window_closed)
                self.windows[len_window].Moved_to_signal.connect(self._on_card_moved)
                self.windows[len_window].show()
                
            elif action == Delete_action:
                if len(os.listdir("Collections")) > 1:
                    path = f"Collections\\{text}.json"
                    try:
                        index = self.collection_combo_box.findText(text)
                        if index != -1:
                            os.remove(path)
                            self.collection_combo_box.removeItem(index)
                    except FileNotFoundError:
                        print("File doesn't exist, nothing to delete")
            elif action == Upload_action:
                file_path, _ = QFileDialog.getOpenFileName( 
                                None, 
                                "Select a file", 
                                "", 
                                "Text Files (*.txt)" 
                            )
                
                if file_path != "":
                    self.msgBox = QMessageBox(self)
                    self.msgBox.setWindowTitle("Download")
                    self.msgBox.setText("<div style='text-align: center;'>Downloading...</div>")
                    self.msgBox.setInformativeText("<div style='text-align: Bottom;'><font size='2'>This will only take a few seconds.</font></div>")

                    self.msgBox.setStandardButtons(QMessageBox.StandardButton.NoButton)

                    self.msgBox.show()
                    self.thread = QThread()
                    self.worker = Worker(file_path,target_file=f"Collections\\{text}.json")
                    self.worker.moveToThread(self.thread)

                    self.thread.started.connect(self.worker.run)
                    self.worker.finished.connect(self.on_download_finished)
                    self.worker.error.connect(self.on_download_error)

                    # cleanup
                    self.worker.finished.connect(self.thread.quit)
                    self.worker.finished.connect(self.worker.deleteLater)
                    self.thread.finished.connect(self.thread.deleteLater)

                    self.thread.start()
    def eventFilter(self,obj,event):
        if event.type() == QEvent.Type.MouseButtonPress:
            if isinstance(obj,QComboBox) and event.button() == Qt.RightButton:
                self.Add_box_item(pos=event.globalPos())
            elif obj is self.collection_combo_box.view().viewport():
                if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease, QEvent.Type.MouseButtonDblClick):

                    if event.button() != Qt.LeftButton:
                                     
                                    print("right clicked")
                                    self.collection_combo_box._suppress_next_hide = True
                                    view = self.collection_combo_box.view()
                                    index = view.indexAt(event.pos())
                                    
                                    if index.isValid():
                                        item_text = self.collection_combo_box.itemText(index.row())
                                        print(f"Right-clicked: {item_text}")
                                        if item_text == Get_Collection().replace("Collections\\","").replace(".json",""):
                                            self.Add_box_item(pos=event.globalPos())
                                        else:
                                            self.drop_down_Add_box_item(item_text, event.globalPos())

                                    
            else:
                for key,widget in self.card_widgets.items():
                    if widget == obj:
                        now = time.time() * 1000  
                        if now - self.last_click_time < self.debounce_ms:
                            return
                        if event.button() == Qt.LeftButton:
                            print(getattr(obj,"custom_data",None)["card_data"]["scryfall_uri"])
                            webbrowser.open(getattr(obj,"custom_data",None)["card_data"]["scryfall_uri"])
                        elif "card_faces" in getattr(obj,"custom_data",None)["card_data"]:
                            self.show_card_menu(key=key,widget=widget,pos=event.globalPos(),double_face=True,obj=obj)
                        else:
                            self.show_card_menu(key,widget,event.globalPos(),obj=obj)
                        break
            print("clicked")
    def _on_upload_into_current_finished(self):
        self.on_download_finished()
        current_name = os.path.splitext(os.path.basename(Get_Collection()))[0]
        if Get_Collection().replace("Collections\\","").replace(".json","") == current_name:
            with open(Get_Collection(), 'r') as file:
                self.cards = json.load(file)
        self.Update_Cards()
        self.update_display(None)
        self._start_next_download()
    def Add_box_item(self,pos):
            if not self.additional_window:
                menu = QMenu(self)
                action_add = menu.addAction("New")
                Upload_action = menu.addAction("Import")
                action_Export = menu.addAction("Export")
                action_Rename = menu.addAction("Rename")
                action_clr = menu.addAction("Clear")
                action_del = menu.addAction("Delete")
                action = menu.exec(pos)
                if action == action_add:
                    self.add_popup = Add_collection_pop_up()
                    self.add_popup.added_collection.connect(self._on_new_collection_added)
                elif action == action_Rename:
                                 self.popup = Rename_collection_pop_up(Get_Collection().replace("Collections\\","").replace(".json",""))
                                 self.popup.renamed.connect(self._on_collection_renamed)
                elif action == action_clr:
                    self.cards = {}
                    self.stop_downloads
                    for key, widget in list(self.card_widgets.items()):
                        self.btnbox.removeWidget(widget)
                        widget.removeEventFilter(self)
                        widget.setParent(None)
                        widget.deleteLater()
                    self.card_widgets.clear()
                    self.card_objs.clear()

                    with open(Get_Collection(),"w") as file:
                        json.dump(self.cards, file, indent=4)
                    self.update_display(None)
                elif action == action_del:
                    if len(os.listdir("Collections")) > 1:
                        path = Get_Collection()
                        try:
                            index = self.collection_combo_box.currentIndex()
                            new_index = index
                            if index < 1:
                                new_index = 1
                                self.collection_combo_box.setCurrentIndex(new_index)
                            else:
                                self.collection_combo_box.setCurrentIndex(new_index-1)
                            os.remove(path)
                            self.collection_combo_box.removeItem(index)
                        except FileNotFoundError:
                            print("File doesn't exist, nothing to delete")
                elif action == action_Export:
                                    exported = ""
                                    with open(self._current_file_path(),"r") as file:
                                        dict_cards = json.load(file)
                                        for key,val in dict_cards.items():
                                            exported = exported+"1 "+key+"\n"
                                        folder_path,_ = QFileDialog.getSaveFileName( 
                                                                                    None, 
                                                                                    "Select a folder", 
                                                                                    "", 
                                                                                    "txt Files (*.txt)"
                                        )
                                        print(f"exported to {folder_path}/exported")
                                    data = f"{folder_path}/{self._current_file_path().replace("Collections\\","").replace(".json","")} collection export"
                                    if folder_path != "":
                                        with open(folder_path,"w") as file:
                                            file.write(exported)
                elif action == Upload_action:
                            file_path, _ = QFileDialog.getOpenFileName( 
                                            None, 
                                            "Select a file", 
                                            "", 
                                            "Text Files (*.txt)" 
                                        )
                            
                            if file_path != "":
                                        self.msgBox = QMessageBox(self)
                                        self.msgBox.setWindowTitle("Download")
                                        self.msgBox.setText("<div style='text-align: center;'>Downloading...</div>")
                                        self.msgBox.setInformativeText("<div style='text-align: Bottom;'><font size='2'>This will only take a few seconds.</font></div>")

                                        self.msgBox.setStandardButtons(QMessageBox.StandardButton.NoButton)

                                        self.msgBox.show()
                                        self.thread = QThread()
                                        self.worker = Worker(file_path,target_file=Get_Collection())
                                        self.worker.moveToThread(self.thread)

                                        self.thread.started.connect(self.worker.run)
                                        self.worker.finished.connect(self._on_upload_into_current_finished)
                                        self.worker.error.connect(self.on_download_error)

                                        # cleanup
                                        self.worker.finished.connect(self.thread.quit)
                                        self.worker.finished.connect(self.worker.deleteLater)
                                        self.thread.finished.connect(self.thread.deleteLater)
                                        self.stop_downloads()

                                        self.thread.start()
                                        
                            
    def Refresh(self):
            self.stop_downloads()
            with open(self._current_file_path(), 'r') as file:
                self.cards = json.load(file)
            self.Update_Cards()
            self.update_display()
            self._start_next_download()
    def Update_Cards(self):
            for index, key in enumerate(sorted(self.cards.keys(),key=self.get_sort_func_by_name(),reverse=self.sort_reverse)):
                if key in self.card_widgets:
                    continue
                row = index // 4
                col = index % 4
                card_widget = QWidget()
                card_widget.setFixedSize(140, 180)

                card_layout = QVBoxLayout(card_widget)
                card_layout.setContentsMargins(5, 5, 5, 5)
                card_layout.setSpacing(5)



                img_label = QLabel()
                img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                img_label.setStyleSheet("border: 1px solid #ccc; border-radius: 4px; background-color: #f0f0f0;")
                

                text_label = QLabel(key)
                text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                text_label.setWordWrap(True)
                text_label.setStyleSheet("font-size: 10px; font-weight: bold; color: #F2F3F5;")

                card_layout.addWidget(img_label)
                card_layout.addWidget(text_label)

                card_widget.setStyleSheet("""
                    QWidget:hover { background-color: #353839; border-radius: 6px; }
                """)

                card_widget.installEventFilter(self)

                self.btnbox.addWidget(card_widget,row,col) 

                self.card_widgets[key] = card_widget

                card_data = self.cards[key]
                self.card_objs.append(card_widget)
                card_widget.custom_data = {"key":key,"card_data":card_data,"img label":img_label,"card face":0}
                FALLBACK_URL = "https://cards.scryfall.io/normal/front/2/9/294e0651-99b4-4792-8ee8-107e7484117d.jpg?1786005602"

                image_dict = card_data.get('image_uris')
                if not image_dict:
                    print(f"No image_uris for {key}, falling back to placeholder")
                if not image_dict and 'card_faces' in card_data:
                    image_dict = card_data['card_faces'][0].get('image_uris')
                img_url = (image_dict or {}).get('normal') or FALLBACK_URL
                self.download_queue.append((img_url, img_label, card_widget))
    def _on_new_collection_added(self,name):
        if name not in [self.collection_combo_box.itemText(i) for i in range(self.collection_combo_box.count())]:
            self.collection_combo_box.addItem(name)
            index = self.collection_combo_box.findText(name)
            if index != -1:
                self.collection_combo_box.setCurrentIndex(index)
    def show_card_menu(self,key,widget,pos,double_face=False,obj=None):
        menu = QMenu(self)
        card_data = self.cards[key]
        items = {}
        open_menu = QMenu(title="Open on")

        move_menu = QMenu(title="Move to")
        for filename in os.listdir("Collections"):
            if filename.endswith(".json"):
                        if filename != self._current_file_path().replace("Collections\\",""):
                            name = filename.replace(".json", "")
                            action_obj = move_menu.addAction(name)
                            items[action_obj] = name

        scryFall_action = open_menu.addAction("Scryfall")
        edhrec_action = open_menu.addAction("EDHREC")
        tcgplayer_action = open_menu.addAction("TCGplayer")
        menu.addMenu(open_menu)
        menu.addMenu(move_menu)
        flip_action = False
        if double_face == True:
            flip_action = menu.addAction("Flip")
        Delete_action = menu.addAction("Delete")


        action = menu.exec(pos)
        if action in items:
            target_name = items[action]
            target_path = f"Collections\\{target_name}.json"
            if os.path.exists(target_path):
                target_name = items[action]
                target_path = f"Collections\\{target_name}.json"
                with open(target_path,"r") as file:
                    old_cards = json.load(file)
                    print("TARGET FILE BEFORE MOVE:", list(old_cards.keys()))   # <-- add this
                    old_cards[key] = card_data
                    print("TARGET FILE AFTER MERGE:", list(old_cards.keys()))   # <-- add this

                with open(target_path,"w") as file:
                    json.dump(old_cards, file, indent=4)
                print(items[action])
                self.cards = card_del(self.cards,key,self._current_file_path())
                widget = self.card_widgets.pop(key, None)
                if widget is not None:
                    if widget in self.card_objs:
                        self.card_objs.remove(widget)
                    self.btnbox.removeWidget(widget)
                    widget.removeEventFilter(self)
                    widget.setParent(None)
                    widget.deleteLater()
                move_bus.moved.emit(target_name)
                self.update_display(self.searchbar.text())
        elif action == scryFall_action:
            webbrowser.open(card_data["scryfall_uri"])
        elif action == edhrec_action:
            webbrowser.open(card_data["related_uris"]["edhrec"])
        elif action == tcgplayer_action:
            webbrowser.open(card_data["purchase_uris"]["tcgplayer"])
        elif action == Delete_action:
            self.cards = card_del(self.cards,key,self._current_file_path())
            widget = self.card_widgets.pop(key, None)
            if widget is not None:
                if widget in self.card_objs:
                    self.card_objs.remove(widget)
                self.btnbox.removeWidget(widget)
                widget.removeEventFilter(self)
                widget.setParent(None)
                widget.deleteLater()
            self.update_display(self.searchbar.text())
        elif action == flip_action:
            if getattr(obj,"custom_data",None)["card face"] == 0:
                self.download_queue.append((card_data['card_faces'][1]["image_uris"]["normal"], getattr(obj,"custom_data",None)["img label"], widget))
                
            else:
                self.download_queue.append((card_data['card_faces'][0]["image_uris"]["normal"], getattr(obj,"custom_data",None)["img label"], widget))
            obj.custom_data["card face"] = not getattr(obj,"custom_data",None)["card face"]
            self.update_display(self.searchbar.text())
            self._start_next_download()
        else:
            pass
    def _current_file_path(self):
        if self.additional_window:
            return f"Collections\\{self.additional_window}.json"
        return Get_Collection()        
    def fade_out_and_close(self):
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(250) 
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self.anim.finished.connect(self.final_close)
        self.anim.start()
    def final_close(self):
        if self.true_close and self.on_final_close:
            self.on_final_close()
        self.hide()
class AdditionalCollection(Collection):
    def __init__(self, on_final_close=None, additional_window=False):
        super().__init__(on_final_close, additional_window)
        self.Moved_to_signal.connect(self._on_card_moved_here)
    def closeEvent(self, event):
            event.ignore()
            self.stop_downloads()
            try:
                for i in self.windows:
                    i.close()
            except Exception as e:
                print(e)
            self.Additional_closed_signal.emit(self.collection_combo_box.currentText())
            self.fade_out_and_close() 
    def show_card_menu(self,key,widget,pos,double_face=False,obj=None):
            menu = QMenu(self)
            card_data = self.cards[key]
            items = {}
            open_menu = QMenu(title="Open on")
    
            move_menu = QMenu(title="Move to")
            for filename in os.listdir("Collections"):
                if filename.endswith(".json"):
                            name = filename.replace(".json", "")
                            action_obj = move_menu.addAction(name)
                            items[action_obj] = name
    
            scryFall_action = open_menu.addAction("Scryfall")
            edhrec_action = open_menu.addAction("EDHREC")
            tcgplayer_action = open_menu.addAction("TCGplayer")
            menu.addMenu(open_menu)
            menu.addMenu(move_menu)
            flip_action = False
            if double_face == True:
                flip_action = menu.addAction("Flip")
            Delete_action = menu.addAction("Delete")
    
    
            action = menu.exec(pos)
            if action in items:
                target_name = items[action]
                target_path = f"Collections\\{target_name}.json"
                if os.path.exists(target_path):
                    target_name = items[action]
                    target_path = f"Collections\\{target_name}.json"
                    with open(target_path,"r") as file:
                        if filename.replace(".json","") != self._current_file_path().replace("Collections\\",""):
                            old_cards = json.load(file)
                            print("TARGET FILE BEFORE MOVE:", list(old_cards.keys()))   # <-- add this
                            old_cards[key] = card_data
                            print("TARGET FILE AFTER MERGE:", list(old_cards.keys()))   # <-- add this
    
                    with open(target_path,"w") as file:
                        json.dump(old_cards, file, indent=4)
                    print(items[action])
                    self.cards = card_del(self.cards,key,self._current_file_path())
                    widget = self.card_widgets.pop(key, None)
                    if widget is not None:
                        if widget in self.card_objs:
                            self.card_objs.remove(widget)
                        self.btnbox.removeWidget(widget)
                        widget.removeEventFilter(self)
                        widget.setParent(None)
                        widget.deleteLater()
                    self.Moved_to_signal.emit(target_name)
                    move_bus.moved.emit(target_name)
                    self.update_display(self.searchbar.text())
                    
            elif action == scryFall_action:
                webbrowser.open(card_data["scryfall_uri"])
            elif action == edhrec_action:
                webbrowser.open(card_data["related_uris"]["edhrec"])
            elif action == tcgplayer_action:
                webbrowser.open(card_data["purchase_uris"]["tcgplayer"])
            elif action == Delete_action:
                self.cards = card_del(self.cards,key,self._current_file_path())
                widget = self.card_widgets.pop(key, None)
                if widget is not None:
                    if widget in self.card_objs:
                        self.card_objs.remove(widget)
                    self.btnbox.removeWidget(widget)
                    widget.removeEventFilter(self)
                    widget.setParent(None)
                    widget.deleteLater()
                self.update_display(self.searchbar.text())
            elif action == flip_action:
                if getattr(obj,"custom_data",None)["card face"] == 0:
                    self.download_queue.append((card_data['card_faces'][1]["image_uris"]["normal"], getattr(obj,"custom_data",None)["img label"], widget))
                    
                else:
                    self.download_queue.append((card_data['card_faces'][0]["image_uris"]["normal"], getattr(obj,"custom_data",None)["img label"], widget))
                obj.custom_data["card face"] = not getattr(obj,"custom_data",None)["card face"]
                self.update_display(self.searchbar.text())
                self._start_next_download()
            else:
                pass
if __name__ == "__main__":
 
    window = MainWindow() 
    window.show() 
    app.exec()
