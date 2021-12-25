from PyQt5 import QtWidgets, uic
import sys
import math

import constants
import recipies
import signal

from PyQt5.QtCore import QCoreApplication

class Ui(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Ui, self).__init__()
        #self.ui = loadUI(os.path.join(root, 'NW_TP3.ui'), baseinstance=self)
        uic.loadUi('NW_TP3.ui', self)
        self.setWindowTitle("New World Trading Post")
        self.buyCombo = self.findChild(QtWidgets.QComboBox,"buy_comboBox")
        self.buyCombo.currentTextChanged.connect(self.buy_combo_selected)
        self.sellCombo = self.findChild(QtWidgets.QComboBox, "sell_comboBox")
        self.sellCombo.currentTextChanged.connect(self.sell_combo_selected)
        self.buyQuantity = self.findChild(QtWidgets.QLineEdit, "buyQuantity")
        self.buyIndividual = self.findChild(QtWidgets.QLineEdit, "buyIndividual")
        self.buyFlip = self.findChild(QtWidgets.QLineEdit, "buyFlip")
        self.capital = self.findChild(QtWidgets.QLineEdit, "Capital")
        self.debug = self.findChild(QtWidgets.QTextEdit, "debug")
        self.show()

    def sell_combo_selected(self):
        item = self.sellCombo.currentText()
        trans_item = lookup_dump_data(item)
        print("FOUND: " + trans_item)
        output = recipies.print_results(str(trans_item))
        self.debug.setText(str(output))

    def buy_combo_selected(self):
        item = self.buyCombo.currentText()

        #TODO:  Add Error Checking for Capital.  MUST ONLY BE POSITIVE Float
        
        buy_individual, buy_profit, buy_price, sell_price, captial = 0.0 , 0.0, 0.0, 0.0, 0.0
        can_buy = 0
        transpose = ""

        capital = float(self.capital.text())

        for line in line_list:
            if item == line[0]:
                buy_price = float(line[1])
                sell_price = float(line[2])
                break

        can_buy = math.floor(capital /buy_price)
        buy_individual = sell_price * can_buy
        buy_profit =  buy_individual - capital
        print("You Selected: " + item)
        for line in dict:
            if line[1] == item:
                transpose = line[0]
                break
        self.buyQuantity.setText(str(can_buy))
        self.buyIndividual.setText(str(buy_individual))
        self.buyFlip.setText(str(buy_profit))

def lookup_dump_data(item):
    dict = constants.dict
    trans_item = ""
    for piece in dict:
        if item == piece[1]:
            trans_item  = piece[0]
            break
    return trans_item

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    line_list = []
    dict = constants.dict

    with open("Ingredients.txt", "r") as read_file:
        lines = read_file.readlines()
    for line in lines:
        as_list = line.split(",")
        line_list.append(as_list) 
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    window.show()
    app.exec_()





