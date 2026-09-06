from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QWidget, QHBoxLayout, QPushButton,QFileDialog,QMessageBox,QVBoxLayout,
QScrollArea,QGridLayout,QLineEdit,QComboBox)
from PySide6.QtGui import QIcon,QPixmap,QMouseEvent
from PySide6.QtCore import Qt,QSize,QTimer
from store_cards import card_dump,card_del
from PySide6.QtCore import Qt, QThread, Signal,QPropertyAnimation, QEasingCurve,QUrl,QEvent
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
class MainWindow(QMainWindow): 
    def __init__(self): 
        super().__init__() 
        self.setWindowTitle("Menu")
        self.setWindowIcon(QIcon("images\Window_icon_circle.png"))
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
            QApplication.processEvents()
            card_dump(win=file_path,Error=False) 

            self.msgBox.setText("<div style='text-align: center;'>Download finished</div>")
            self.msgBox.setInformativeText("")
            self.msgBox.setStandardButtons(QMessageBox.StandardButton.Ok)
            self.msgBox.close()
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
class Settings(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("images/Cog_wheel_icon.png"))
        self.setWindowTitle("Settings")
        self.main_layout = QVBoxLayout(self)  
        self.Collection_name = QLabel("")
        self.Collection_label = QLabel("Collection Name:")
        self.name = QLineEdit(placeholderText=str(Get_Collection().removesuffix(".json").lstrip("Collections")).replace("\\",""))
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
class Collection(QWidget):

    closed_signal = Signal()

    def __init__(self,on_final_close=None):
        super().__init__()
        self.card_objs = []
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
        self.setWindowIcon(QIcon("images\Window_icon_circle.png"))
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

        self.collection_combo_box = QComboBox()
        for filename in os.listdir("Collections"):
            if filename.endswith(".json"):
                name = filename.removesuffix(".json")
                self.collection_combo_box.addItem(name)
        current_name = os.path.splitext(os.path.basename(Get_Collection()))[0]
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
        self.sort.addItems(["Name", "Mana Value", "Power","Toughness"])
        self.sort.currentTextChanged.connect(self.filter_change)

        self.sort_dir = QPushButton()
        self.sort_dir.setIcon(QIcon("images/down_arrow_rounded.png"))
        self.sort_dir.clicked.connect(self.filter_dir)
        self.sort_dir.setFixedSize(QSize(25,25))
        self.sort_dir.setIconSize(self.sort_dir.size())
        self.btnbox.setSpacing(15)
        self.network_manager = QNetworkAccessManager(self)


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
        window_layout.addWidget(self.collection_combo_box)
        window_h_layout.addWidget(self.searchbar)
        window_h_layout.addWidget(self.sort)
        window_h_layout.addWidget(self.sort_dir)
        window_layout.addLayout(window_h_layout) 


        self.scroll.setWidget(container_widget)
        window_layout.addWidget(self.scroll)
        self._start_next_download()
    def change_collection(self):
        Set_Collection(self.collection_combo_box.currentText())
        self.stop_downloads()
        self.true_close = False
        self.close()
        self.new_collection_window = Collection(on_final_close=self.on_final_close)
        self.new_collection_window.show()
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
        except:
                    self.fade_out_and_close()
            
        self._current_reply = None
    def update_display(self,text):
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
                print(f"Network error: {reply.errorString()}")
                if isValid(label):
                    label.setText("Error loading")
        finally:
            if isValid(reply):
                    reply.deleteLater()
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
        self.fade_out_and_close()



    def eventFilter(self,obj,event):
        if event.type() == QEvent.Type.MouseButtonPress:
            for key,widget in self.card_widgets.items():
                if widget == obj:
                    now = time.time() * 1000  
                    if now - self.last_click_time < self.debounce_ms:
                        return
                    if event.button() == Qt.LeftButton:
                        print(getattr(obj,"custom_data",None)["card_data"]["scryfall_uri"])
                        webbrowser.open(getattr(obj,"custom_data",None)["card_data"]["scryfall_uri"])
                    else:
                        self.cards = card_del(self.cards,key)
                        widget = self.card_widgets.pop(key, None)
                        if widget is not None:
                            if widget in self.card_objs:
                                self.card_objs.remove(widget)
                            self.btnbox.removeWidget(widget)
                            widget.removeEventFilter(self)
                            widget.setParent(None)
                            widget.deleteLater()
                        self.update_display(self.searchbar.text())
                    break
            print("clicked")

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

if __name__ == "__main__":
 
    window = MainWindow() 
    window.show() 
    app.exec()
