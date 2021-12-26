import math
import signal
import sys

from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QDoubleValidator, QStandardItemModel, QStandardItem

import constants
import recipes

#  Global variables
#  Setting global variables here caused interesting issues
#  however setting them global further down (line 88 for total_ingr_cost) works fine
total_ingr_cost = 0.0


class Ui(QtWidgets.QWidget):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('../config/NW_TP3.ui', self)
        self.setWindowTitle("New World Trading Post")

        #
        # Initialize components
        #
        self.buyCombo = self.findChild(QtWidgets.QComboBox, "buy_comboBox")
        self.buyCombo.currentTextChanged.connect(self.buy_combo_selected)
        self.sellCombo = self.findChild(QtWidgets.QComboBox, "sell_comboBox")
        self.sellCombo.currentTextChanged.connect(self.sell_combo_selected)
        self.buyQuantity = self.findChild(QtWidgets.QLineEdit, "buyQuantity")
        self.buyQuantity.setReadOnly(True)
        self.sellQuantity = self.findChild(QtWidgets.QLineEdit, "sellQuantity")
        self.sellQuantity.setReadOnly(True)
        self.buyIndividual = self.findChild(QtWidgets.QLineEdit, "buyIndividual")
        self.buyIndividual.setReadOnly(True)
        self.sellIndividual = self.findChild(QtWidgets.QLineEdit, "sellIndividual")
        self.sellIndividual.setReadOnly(True)
        self.buyFlip = self.findChild(QtWidgets.QLineEdit, "buyFlip")
        self.buyFlip.setReadOnly(True)
        self.sellFlip = self.findChild(QtWidgets.QLineEdit, "sellFlip")
        self.sellFlip.setReadOnly(True)
        self.capital = self.findChild(QtWidgets.QLineEdit, "Capital")
        self.onlyDouble = QDoubleValidator(0.0, 500000.00, 2)
        # Validate capital input (min, max, decimal) Max not working as intended
        self.capital.setValidator(self.onlyDouble)
        self.debug = self.findChild(QtWidgets.QTextEdit, "debug")
        self.debug_tree = self.findChild(QtWidgets.QTreeView, "debugTreeView")
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Recipe", "Qty", "Cost", "Total Qty", "Total Cost"])
        self.debug_tree.header().setDefaultSectionSize(180)
        self.debug_tree.setModel(self.model)
        self.debug_tree.setColumnWidth(0, 150)
        self.debug_tree.setColumnWidth(1, 50)
        self.debug_tree.setColumnWidth(2, 50)
        #
        # End component initialization
        #

        self.show()

    def sell_combo_selected(self):
        can_make,  sell_individual, sell_flip = 0.0, 0.0, 0.0

        item = self.sellCombo.currentText()
        trans_item = lookup_dump_data(item)
        print("LOOKUP: " + item)
        print("FOUND: " + trans_item)
        output = recipes.print_results(str(trans_item))

        self.process_output(output)  # Fill QTreeView
        self.debug.setText(str(output))  # Fill RichTextBox
        # TODO:  Verify formulas for sell boxes
        capital = float(self.capital.text())

        can_make = math.floor(capital / total_ingr_cost)  # Formulate and set sell quantity ( qty can be made )
        self.sellQuantity.setText(str(can_make))
        p = lookup_prices(item)

        sell_individual = can_make * float(p[1])  # Formulate and set sell individual
        self.sellIndividual.setText(str(sell_individual))

        sell_flip = sell_individual - capital  # Formulate and set sell flip
        self.sellFlip.setText(str(sell_flip))

    def process_output(self, data_in):
        self.model.setRowCount(0)
        global total_ingr_cost
        total_ingr_cost = 0
        recipe_split = data_in.split("\n")

        #  Iterate recipes within string
        for r in recipe_split:
            parent = QStandardItem(r.split(":")[0])  # Split recipe name from ingredients
            parent.setEditable(False)
            ingrs = r.split(":")[1]  # Split ingredients from recipe name

            # Iterate ingredients in recipe and split ingr from qty
            for i in ingrs.split(","):
                t = i.split("-")
                # For loop causes index out of range when using t[1] outside of try except, unsure why
                try:
                    ingr = QStandardItem(t[1])
                    qty = QStandardItem(t[0])
                    ingr.setEditable(False)
                    qty.setEditable(False)

                    p = lookup_prices(t[1])
                    cost = float(p[0]) * float(t[0])
                    total_ingr_cost += cost
                    buy_price = QStandardItem(str(cost))

                    parent.appendRow([
                        ingr, qty, buy_price  # ingr col1: qty col2: buy price col3
                    ])
                except IndexError:
                    print("Index Error")

            self.model.appendRow(parent)
            self.debug_tree.expandAll()

    def buy_combo_selected(self):
        item = self.buyCombo.currentText()
        capital = float(self.capital.text())
        can_buy, buy_individual, buy_flip = 0.0, 0.0, 0.0

        p = lookup_prices(item)
        buy_price, sell_price = p[0], p[1]

        can_buy = math.floor(capital / buy_price)
        buy_individual = sell_price * can_buy
        buy_profit = buy_individual - capital
        self.buyQuantity.setText(str(can_buy))
        self.buyIndividual.setText(str(buy_individual))
        self.buyFlip.setText(str(buy_profit))


def lookup_dump_data(item):
    dict = constants.dict
    trans_item = ""
    for piece in dict:
        if item == piece[1]:
            trans_item = piece[0]
            break
    return trans_item


def lookup_prices(item):
    price_list = []
    for elem in line_list:
        if item == elem[0]:
            price_list.append(float(elem[1]))
            price_list.append(float(elem[2]))
            break
    return price_list


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    line_list = []
    dict = constants.dict

    with open(constants.INGREDIENTS, "r") as read_file:
        lines = read_file.readlines()
    for line in lines:
        as_list = line.split(",")
        line_list.append(as_list)

    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    window.show()
    app.exec_()
