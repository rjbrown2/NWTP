import math
import signal
import sys
import webbrowser

from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtGui import QDoubleValidator, QStandardItemModel, QStandardItem, QFont
from PyQt5.QtWidgets import QMenuBar, QAction, QMessageBox

import constants
import recipes

import market_data


class Ui(QtWidgets.QWidget):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('../config/NW_TP3.ui', self)
        self.setWindowTitle("New World Trading Post")
        self.debug_tree = self.findChild(QtWidgets.QTreeView, "debugTreeView")
        self.menu_bar = QMenuBar(self)
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
        self.create_menus()

    def create_menus(self):
        files_menu = self.menu_bar.addMenu("Files")
        reset_market = files_menu.addAction("Reset market data")
        reset_market.triggered.connect(self.fetch_market_action)

        help_menu = self.menu_bar.addMenu("Help")
        report_issue = help_menu.addAction("Report Issue")
        report_issue.triggered.connect(self.report_action)

        help_menu.addAction("Read me")

        about = help_menu.addAction("About")
        about.triggered.connect(self.about_action)

    def read_me_action(self):
        pass

    def about_action(self):
        about_dialog = QMessageBox()
        about_dialog.setWindowTitle("About this application")
        about_dialog.setText("THIS WAS FUCKING PAINFUL")
        about_dialog.exec()
        pass

    def report_action(self):
        webbrowser.open("https://github.com/rjbrown2/NWTP/issues/new")

    def fetch_market_action(self):
        market_data.fetch_market_data()

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
        if self.capital.text() != "" and float(self.capital.text()) > 500000.00:
            self.capital.setText(str(500000.00))
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
        # item2 = self.buyCombo.currentText() # TODO:  Logic to make sure the box has something
        trans_item = lookup_dump_data(item)
        # trans_item2 = lookup_dump_data(item2)
        test_recipe = recipes.pull_recipe(trans_item)  # TODO:  Fix to work with item2
        # TODO: here
        self.eliminate_unused(test_recipe)
        self.populate_treeview(test_recipe)  # Fill QTreeView
        print("RECIPE NAME: ", str(test_recipe.common_name))
        print("CRAFT PRICE: " + str(test_recipe.craft_price))

    def fill_tree_values(self):
        index = self.parent_indexes
        some_name = "Linen"
        mult_quantity = False
        mult_amount = 0
        k = 0
        for i in index:
            if isinstance(i, list):
                for j in i:
                    if isinstance(j, list):
                        if self.model.itemFromIndex(j[0]).text() == some_name:
                            mult_amount = int(self.model.itemFromIndex(j[1]).text())
                        qty = self.model.itemFromIndex(j[1])
                        price = self.model.itemFromIndex(j[2])
                        t_qty = self.model.itemFromIndex(j[3])
                        t_cost = self.model.itemFromIndex(j[4])
                        if mult_quantity:
                            temp_qty = int(float(qty.text())) * mult_amount
                            temp_cost = float(price.text()) * mult_amount
                        else:
                            temp_qty = int(float(qty.text()))
                            temp_cost = float(price.text())
                        total_quantity = temp_qty * self.can_make  # Total qty = qty * can make
                        total_cost = self.can_make * temp_cost  # Total cost = total qty * cost
                        self.model.setData(t_qty.index(), total_quantity)
                        self.model.setData(t_cost.index(), total_cost)
            else:
                if self.model.item(k,0).text() == some_name:
                    mult_quantity = True
                k += 1

    def populate_treeview(self, data_in):
        self.model.setRowCount(0)
        self.total_ingr_cost = 0
        recipe = data_in
        self.parent_indexes = []  # Parent index list
        loop_trigger = True
        children = []  # Children index list
        while loop_trigger:
            children = []
            loop_trigger = recipe.has_sub_recipe
            parent_font = QFont("Segoe UI", 9, QFont.Bold)
            parent = QStandardItem(recipe.common_name)  # Parent Creation
            parent.setFont(parent_font)
            self.parent_indexes.append(parent.index())
            parent.setEditable(False)
            recipe_string = QStandardItem(str(recipe.buy_price))
            recipe_string.setFont(parent_font)
            self.model.appendRow([parent, QStandardItem(""), recipe_string])
            ingr_list = recipe.ingrs

            for _i in ingr_list:
                ingr = QStandardItem(_i.common_name)
                qty = QStandardItem(_i.qty)

                cost = float(_i.buy_price) * int(_i.qty)  # Cost = Buy Price * Qty
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

        # can_make = math.floor(capital / self.total_ingr_cost)  # Formulate and set sell quantity ( qty can be made )
        # self.can_make = can_make
        # self.sellQuantity.setText(str(can_make))
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

    def eliminate_unused(self, rec):  # TODO: Rename this
        buy_item, name, buy_price, make_price = make_or_buy(rec)
        # TODO: left buy_price here because I might want to do something with it.  If not remove it later.
        total_cost = 0
        if buy_item:  # If we're buying the item, use that price in calculations
            text = "You should <b><u><font color = \"Red\">BUY</font></u></b> the <u><b>" + \
                   name + "</b></u> from the <i>Selling</i> box for maximum profit."
        else:   # Crafting the item
            text = "You should <b><u><font color = \"Red\">CRAFT</font></u></b> the <u><b>" + \
                   name + "</b></u> from the <i>Selling</i> box for the maximum profit."

        self.text_info.setText(text)
        loop_val = True
        while loop_val:
            if rec.has_sub_recipe:
                if rec.sub_recipe.common_name == name:
                    loop_val = False
            else:
                loop_val = False
            for i in rec.ingrs:
                this_price = i.buy_price
                if i.common_name == name:
                    if not buy_item:    # Crafting the item
                        this_price = make_price
                        i.buy_price = make_price
                    else:               # Buying the item
                        # this_price = buy_price
                        pass
                total_cost += float(i.buy_price) * int(i.qty)
            rec = rec.sub_recipe
        if self.capital.text() == "":
            self.reset_sell()
            return
        can_make = math.floor(float(self.capital.text()) / total_cost)
        self.sellQuantity.setText(str(can_make))
        self.can_make = can_make


def make_or_buy(rec):
    buy_item = False
    make_price, buy_price, common_name = lowest_parent_recipe(rec)
    if make_price > buy_price:
        buy_item = True
    return buy_item, common_name, buy_price, make_price


def lowest_parent_recipe(rec):
    while rec.has_sub_recipe:
        rec = rec.sub_recipe
    cost_of_one = int(rec.ingrs[0].qty) * float(rec.ingrs[0].buy_price)
    rec_buy_price = rec.buy_price
    return cost_of_one, rec_buy_price, rec.common_name


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
