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
from src import market_data

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
        self.debug_tree.header().setDefaultSectionSize(410)
        self.debug_tree.setModel(self.model)
        self.debug_tree.setColumnWidth(0, 200)
        self.debug_tree.setColumnWidth(1, 50)
        self.debug_tree.setColumnWidth(2, 50)
        self.debug_tree.setColumnWidth(3, 60)
        self.debug_tree.setColumnWidth(4, 50)
        #
        # End component initialization
        #

        self.show()

    def sell_combo_selected(self):
        can_make, sell_individual, sell_flip = 0.0, 0.0, 0.0

        item = self.sellCombo.currentText()
        trans_item = lookup_dump_data(item)

        self.populate_treeview(recipes.pull_recipe(trans_item))  # Fill QTreeView
        # self.debug.setText(str(output))  # Fill RichTextBox
        # TODO:  Verify formulas for sell boxes
        capital = float(self.capital.text())

        can_make = math.floor(capital / total_ingr_cost)  # Formulate and set sell quantity ( qty can be made )
        self.sellQuantity.setText(str(can_make))
        p = market_data.lookup_prices(item)

        sell_individual = can_make * float(p[1])  # Formulate and set sell individual
        self.sellIndividual.setText(str(sell_individual))

        sell_flip = sell_individual - capital  # Formulate and set sell flip
        self.sellFlip.setText(str(sell_flip))

    # I've removed all of the string processing...cause I'm OCD and don't like it.
    def populate_treeview(self, data_in):
        self.model.setRowCount(0)
        global total_ingr_cost
        total_ingr_cost = 0
        recipe = data_in

        loop_trigger = recipe.hasSubRecipe()

        while loop_trigger:
            loop_trigger = recipe.has_sub_recipe
            parent = QStandardItem(recipe.getRecipeName())
            parent.setEditable(False)

            self.model.appendRow(parent)
            ingr_list = recipe.getIngredients()
            qty_list = recipe.getIngredientQuantities()
            iq_list = [item for sublist in zip(ingr_list, qty_list) for item in sublist]
            for _i, _j in zip(iq_list[::2], iq_list[1::2]):
                price = market_data.lookup_prices(_i)
                qty = QStandardItem(_j)
                ingr = QStandardItem(_i)
                cost = float(price[0]) * int(_j)
                total_ingr_cost += cost
                buy_price = QStandardItem(str(cost))
                total_qty = QStandardItem(str(0))
                total_cost = QStandardItem(str(0))
                parent.appendRow([ingr, qty, buy_price, total_qty, total_cost])

            recipe = recipe.sub_recipe

        self.debug_tree.expandAll()

    def buy_combo_selected(self):
        item = self.buyCombo.currentText()
        capital = float(self.capital.text())
        can_buy, buy_individual, buy_flip = 0.0, 0.0, 0.0

        p = market_data.lookup_prices(item)
        buy_price, sell_price = p[0], p[1]

        can_buy = math.floor(capital / buy_price)
        buy_individual = sell_price * can_buy
        buy_profit = buy_individual - capital
        self.buyQuantity.setText(str(can_buy))
        self.buyIndividual.setText(str(buy_individual))
        self.buyFlip.setText(str(buy_profit))


def lookup_dump_data(item):
    dict = constants.dict
    trans_item = item
    for piece in dict:
        if item == piece[1]:
            trans_item = piece[0]
            break
    return trans_item


if __name__ == "__main__":
    market_data.fetch_market_data()  # Fetch Market Data from google sheets
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    dict = constants.dict

    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    window.show()
    app.exec_()
