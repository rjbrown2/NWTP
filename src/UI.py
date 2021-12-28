import math
import signal
import sys

from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtGui import QDoubleValidator, QStandardItemModel, QStandardItem

import constants
import recipes

import market_data


class Ui(QtWidgets.QWidget):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('../config/NW_TP3.ui', self)
        self.setWindowTitle("New World Trading Post")
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
        self.onlyDouble = QDoubleValidator(0.0, 500000.00, 2)
        self.capital = self.findChild(QtWidgets.QLineEdit, "Capital")
        # Validate capital input (min, max, decimal) Max not working as intended
        self.capital.setValidator(self.onlyDouble)
        self.capital.textEdited.connect(self.update)
        self.text_info = self.findChild(QtWidgets.QLabel, "text_info")
        self.text_info.setAlignment(QtCore.Qt.AlignCenter)
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
        

        self.parent_indexes = []
        self.can_make = 0
        self.total_ingr_cost = 0
        #
        # End component initialization
        #
        self.show()
    
    def reset_sell(self):
        self.model.invisibleRootItem().removeRows(0, self.model.rowCount())  # Clear fields pertaining to sell drop down
        self.sellQuantity.setText("")
        self.sellIndividual.setText("")
        self.sellFlip.setText("")

    def reset_buy(self):
        self.buyQuantity.setText("")
        self.buyIndividual.setText("")
        self.buyFlip.setText("")

    def update(self):
        if self.capital.text() == "":
            self.reset_sell()
            self.reset_buy()
        if self.sellCombo.currentText() != "":
            self.sell_combo_selected()
        if self.buyCombo.currentText() != "":    
            self.buy_combo_selected()

    def sell_combo_selected(self):
        if self.capital.text == "":
            self.reset_sell()
            return

        item = self.sellCombo.currentText()

        if not item:
            self.reset_sell()
            return
        item = self.sellCombo.currentText()
        #item2 = self.buyCombo.currentText() # TODO:  Logic to make sure the box has something
        trans_item = lookup_dump_data(item)
        #trans_item2 = lookup_dump_data(item2)
        test_recipe = recipes.pull_recipe(trans_item) # TODO:  Fix to work with item2
        # TODO: here
        self.eliminate_unused(test_recipe)
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
                        temp_qty = int(float(qty.text()))
                        temp_cost = float(price.text())
                        total_quantity = temp_qty * self.can_make  # Total qty = qty * can make
                        total_cost = self.can_make * temp_cost  # Total cost = total qty * cost
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
        if self.capital.text() == "" or not item:
            self.reset_buy()
            return

        capital = float(self.capital.text())
        can_buy, buy_individual, buy_flip = 0.0, 0.0, 0.0

        p = market_data.lookup_prices(item)
        buy_price, sell_price = p[0], p[1]

        can_buy = math.floor(capital / buy_price)  # Can buy = floor(Capital / buy price)
        buy_individual = sell_price * can_buy  # Buy individual = sell price * can_buy
        buy_profit = buy_individual - capital  # Buy Profit = Buy individual - capital
        self.buyQuantity.setText(str(can_buy))
        self.buyIndividual.setText(str("{:.2f}".format(buy_individual)))

        if buy_profit < 0:
            self.buyFlip.setStyleSheet("color: red;")
        else:
            self.buyFlip.setStyleSheet("color: green;")

        self.buyFlip.setText(str("{:.2f}".format(buy_profit)))

    def do_math(self):
        # TODO:  Verify formulas for sell boxes
        if self.capital.text() == "":
            self.reset_buy()
            self.reset_sell()
            return

        capital = float(self.capital.text())

        item = self.sellCombo.currentText()

        #can_make = math.floor(capital / self.total_ingr_cost)  # Formulate and set sell quantity ( qty can be made )
        #self.can_make = can_make
        #self.sellQuantity.setText(str(can_make))
        p = market_data.lookup_prices(item)

        sell_individual = self.can_make * float(p[1])  # Formulate and set sell individual
        self.sellIndividual.setText(str("{:.2f}".format(sell_individual)))

        sell_flip = sell_individual - capital  # Formulate and set sell flip
        f_sell_flip = "{:.2f}".format(sell_flip)
        if sell_flip < 0:
            self.sellFlip.setStyleSheet("color: red;")
        else:
            self.sellFlip.setStyleSheet("color: green;")
        self.sellFlip.setText(f_sell_flip)
        self.fill_tree_values()
        

    def eliminate_unused(self,rec): #TODO: Rename this?  It's not really eliminating unused.  It's more determining if we should use the "made price" or the "bought price"
        buy_item, name, buy_price, make_price = self.dumbshit(rec)  # TODO: left buy_price here because I might want to do something with it.  If not remove it later.
        total_cost = 0
        if buy_item:    # If we're buying the item, use that price in calculations
            text = "You should <b><u><font color = \"Red\">BUY</font></u></b> the lowest tier recipe item from the <i>Selling</i> box for maximum profit."
            self.text_info.setText(text)
            loop_val = True
            while loop_val:
                if rec.has_sub_recipe:
                    if rec.getSubRecipe().common_name == name:
                        loop_val = False
                else:
                    loop_val = False
                for i in rec.getIngredients():
                    total_cost += float(i.buy_price) * int(i.qty)
                rec = rec.getSubRecipe()
        else:           # If we're making the item, use that price in calculations
            text = "You should <b><u><font color = \"Red\">CRAFT</font></u></b> the lowest tier recipe rom the <i>Selling</i> box for the maximum profit."
            self.text_info.setText(text)
            loop_val = True
            while loop_val:
                for i in rec.getIngredients():
                    this_price = i.buy_price
                    if i.common_name == name:
                        this_price = make_price
                    total_cost += float(this_price) * int(i.qty)
                if rec.has_sub_recipe:
                    rec = rec.getSubRecipe()
                else:
                    loop_val = rec.has_sub_recipe
        if self.capital.text() == "":
            self.reset_sell()
            return
        can_make = math.floor(float(self.capital.text()) / total_cost)
        self.sellQuantity.setText(str(can_make))
        self.can_make = can_make

    def dumbshit(self, rec):
        buy_item = False
        make_price, buy_price, common_name = self.lowest_parent_rec(rec)
        if make_price > buy_price:
            buy_item = True
        return buy_item, common_name, buy_price, make_price

    def lowest_parent_rec(self, rec):
        while rec.hasSubRecipe():
            rec = rec.getSubRecipe()
        costofone = int(rec.getIngredients()[0].getQuantity()) * float(rec.getIngredients()[0].getBuyPrice())
        rec_buy_price = rec.getBuyPrice()
        return costofone, rec_buy_price, rec.common_name



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
