import math
import signal
import sys

from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QDoubleValidator, QStandardItemModel, QStandardItem
from PyQt5.QtCore import QObject, pyqtSignal
import constants
import recipes
import time

#  Global variables
#  Setting global variables here caused interesting issues
#  however setting them global further down (line 88 for total_ingr_cost) works fine
import market_data


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
        self.parent_indexes = []
        self.can_make = 0
        self.total_ingr_cost = 0
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

        if not item:
            # TODO: Change how tree is cleared
            self.model.clear()  # Clear fields pertaining to sell drop down
            self.sellQuantity.setText("")
            self.sellIndividual.setText("")
            self.sellFlip.setText("")
            return
        item = self.sellCombo.currentText()
        trans_item = lookup_dump_data(item)
        test_recipe = recipes.pull_recipe(trans_item)
        # TODO: here
        self.dumbshit(test_recipe)
        self.populate_treeview(recipes.pull_recipe(trans_item))  # Fill QTreeView

    def fill_tree_values(self):
        index = self.parent_indexes
        for i in index:
            if isinstance(i, list):
                for j in i:
                    if isinstance(j, list):
                        qty = self.model.itemFromIndex(j[1])
                        price = self.model.itemFromIndex(j[2])
                        t_qty = self.model.itemFromIndex(j[3])
                        t_cost = self.model.itemFromIndex(j[4])
                        self.temp_qty = int(float(qty.text()))
                        self.temp_cost = float(price.text())
                        total_quantity = self.temp_qty * self.can_make  # Total qty = qty * can make
                        total_cost = total_quantity * self.temp_cost  # Total cost = total qty * cost
                        self.model.setData(t_qty.index(), total_quantity)
                        self.model.setData(t_cost.index(), total_cost)

    def populate_treeview(self, data_in):
        self.model.setRowCount(0)
        self.total_ingr_cost = 0
        recipe = data_in
        self.parent_indexes = []  # Parent index list
        loop_trigger = True
        children = []  # Children index list
        while loop_trigger:
            children = []
            loop_trigger = recipe.hasSubRecipe()
            parent = QStandardItem(recipe.getRecipeName())  # Parent Creation
            self.parent_indexes.append(parent.index())
            parent.setEditable(False)

            self.model.appendRow(parent)
            ingr_list = recipe.getIngredients()

            for _i in ingr_list:
                ingr = QStandardItem(_i.getIngredientName())
                qty = QStandardItem(_i.getQuantity())

                cost = float(_i.getBuyPrice()) * int(_i.getQuantity())  # Cost = Buy Price * Qty
                self.total_ingr_cost += cost  # total_ingr_cost = cost of all ingredients not accounting for conversions

                buy_price = QStandardItem(str(cost))
                buy_price.setEditable(False)

                total_qty = QStandardItem(str(0))
                total_qty.setEditable(False)

                total_cost = QStandardItem(str(0))
                total_cost.setEditable(False)

                parent.appendRow([ingr, qty, buy_price, total_qty, total_cost])  # Child Creation
                children.append([ingr.index(), qty.index(), buy_price.index(), total_qty.index(), total_cost.index()])

            recipe = recipe.sub_recipe
            self.parent_indexes.append(children)  # Append children to parent index
        self.debug_tree.expandAll()

        self.do_math()  # Do fucking math

    def buy_combo_selected(self):
        item = self.buyCombo.currentText()
        capital = float(self.capital.text())
        can_buy, buy_individual, buy_flip = 0.0, 0.0, 0.0

        p = market_data.lookup_prices(item)
        buy_price, sell_price = p[0], p[1]

        can_buy = math.floor(capital / buy_price)  # Can buy = floor(Capital / buy price)
        buy_individual = sell_price * can_buy  # Buy individual = sell price * can_buy
        buy_profit = buy_individual - capital  # Buy Profit = Buy individual - capital
        self.buyQuantity.setText(str(can_buy))
        self.buyIndividual.setText(str(buy_individual))
        self.buyFlip.setText(str(buy_profit))

    def do_math(self):
        # TODO:  Verify formulas for sell boxes
        capital = float(self.capital.text())

        item = self.sellCombo.currentText()

        can_make = math.floor(capital / self.total_ingr_cost)  # Formulate and set sell quantity ( qty can be made )
        self.can_make = can_make
        self.sellQuantity.setText(str(can_make))
        p = market_data.lookup_prices(item)

        sell_individual = can_make * float(p[1])  # Formulate and set sell individual
        self.sellIndividual.setText(str(sell_individual))

        sell_flip = sell_individual - capital  # Formulate and set sell flip
        f_sell_flip = "{:.2f}".format(sell_flip)
        self.sellFlip.setText(f_sell_flip)
        self.fill_tree_values()
        pass

    def eleminate_unused(self):
        pass

    def dumbshit(self, rec):
        buy_recipe = False
        make, buy = self.lowest_parent_rec(rec)
        print(str(make) + " " + str(buy))
        if make > buy:
            buy_recipe = True
        print(buy_recipe)
        return buy_recipe

    def lowest_parent_rec(self, rec):
        while rec.hasSubRecipe():
            rec = rec.getSubRecipe()

        costofone = rec.getIngredients()[0].getQuantity() * rec.getIngredients()[0].getBuyPrice()
        rec_buy = rec.getBuyPrice()
        return costofone, rec_buy



def lookup_dump_data(item, reverse_lookup=False):
    dict = constants.dict
    trans_item = item
    if reverse_lookup:
        i = 0
        while i < 10:
            if item == dict[i][0]:
                trans_item = dict[i][1]
                break
            i += 1
    else:
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
